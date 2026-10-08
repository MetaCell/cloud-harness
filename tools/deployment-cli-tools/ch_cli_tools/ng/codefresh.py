import re
from functools import lru_cache

from .model import CHValues, register_file
from .utils import dict_merge  # type: ignore

KEY_BUILD_PARALLEL = "build_application_images"
KEY_UNIT_TESTS = "tests_unit"
KEY_CLONE_DEPENDENCIES = "post_main_clone"

_INVALID_STEP_KEY_CHARS = re.compile(r"[^a-zA-Z0-9_]")


def _clean_step_key(name: str) -> str:
    return _INVALID_STEP_KEY_CHARS.sub("_", name)


def _git_main_domain(url: str) -> str:
    try:
        host = url.split("//")[1].split("/")[0]
    except IndexError:
        return "${{ DEFAULT_REPO }}"
    if "gitlab" in host:
        return "gitlab"
    if "bitbucket" in host:
        return "bitbucket"
    return "github"


@register_file(
    "codefresh_template",
    lambda root: root / "deployment-configuration" / "codefresh-template.yaml",
)
class CHCodefreshTemplate(CHValues):
    @lru_cache
    def all_values(self):
        layer = self.containing_project
        own = self.merge_with_envs(self.project.config.envs)
        if layer.base is None:
            return own
        return dict_merge(layer.base.codefresh_template.all_values(), own)


@register_file(
    "codefresh", lambda root: root / "deployment" / "codefresh.yaml", only_env=True
)
class CHCodefresh(CHValues):
    def qualify(self, image_name):
        return self.project.qualify(image_name)

    def _context_for(self, entity):
        return entity.dockerfile.resolve_context(self.path.parent).resolve_for_build(
            self.path.parent
        )

    def _build_arguments(self, entity) -> list[str]:
        args: dict[str, str] = {}
        if self.project.config.local or self.project.config.debug:
            args["DEBUG"] = "true"
        for dep in self.project._combined_dependencies(entity):
            if isinstance(dep, str):
                continue
            args[dep.name.upper().replace("-", "_")] = self.qualify(dep.image_name)
        args.update(self.project.all_source_images())
        return [f"{key}={value}" for key, value in args.items()]

    def _collect_build_step(self, entity):
        context = self._context_for(entity)
        step = {
            "title": f"Building {entity.name}",
            "type": "build",
            "image_name": self.qualify(entity.image_name),
            "working_directory": str(context.path),
            "dockerfile": str(context.dockerfile.path),
            "tag": "${{CF_SHORT_REVISION}}",
        }
        build_arguments = self._build_arguments(entity)
        if build_arguments:
            step["build_arguments"] = build_arguments
        # MISSING: a `stage:` assignment (no `stages` pipeline scaffolding is
        # modeled here). `registry_secret_name`/`domain` are on CHDeployConfig
        # now but have nothing to plug into yet either: registry auth for a
        # push is a Codefresh registry integration reference, not a k8s secret
        # name (that's a Helm-values concern), and `domain` only matters for
        # e2e test steps, not generated yet.
        return entity.name, step

    def _collect_git_clone_steps(self, project):
        steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            for dep in app.git_dependencies:
                url = dep["url"]
                branch_tag = dep.get("branch_tag")
                repo_name = url.rsplit("/", 1)[-1]
                step_name = _clean_step_key(f"clone_{repo_name}_{branch_tag}_{app.name}")
                destination = app.path / "dependencies" / (dep.get("path") or "")
                steps[step_name] = {
                    "title": f"Cloning {repo_name} repository...",
                    "type": "git-clone",
                    "repo": url,
                    "revision": branch_tag,
                    "working_directory": str(
                        destination.resolve().relative_to(
                            self.path.parent.resolve(), walk_up=True
                        )
                    ),
                    "git": _git_main_domain(url),
                }
        return steps

    def _collect_task_build_steps(self, app):
        steps = {}
        for task in app.tasks.values():
            if not task.dockerfile.path.exists():
                continue
            key, step = self._collect_build_step(task)
            steps[key] = step
        return steps

    def _collect_base_image_build_steps(self, project):
        steps = {}
        for base_image in project.base_images.values():
            if not base_image.dockerfile.path.exists():
                continue
            key, step = self._collect_build_step(base_image)
            steps[key] = step
        return steps

    def _collect_unit_test_steps(self, project):
        steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            commands = app.test.unit.commands
            if not commands:
                continue
            steps[f"{app.name}_ut"] = {
                "title": f"Unit tests for {app.name}",
                "commands": commands,
                "image": self.qualify(app.image_name),
            }
        return steps

    def generate(self, write_on_disk=True, output_path="."):
        project = self.project

        base = project.codefresh_template.all_values()
        steps = base.setdefault("steps", {})

        build_steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue

            if app.dockerfile.path.exists():
                key, step = self._collect_build_step(app)
                build_steps[key] = step

            build_steps.update(self._collect_task_build_steps(app))
        build_steps.update(self._collect_base_image_build_steps(project))

        steps.setdefault(KEY_BUILD_PARALLEL, {"type": "parallel", "steps": {}})
        steps[KEY_BUILD_PARALLEL].setdefault("steps", {}).update(build_steps)

        unit_test_steps = self._collect_unit_test_steps(project)
        steps.setdefault(KEY_UNIT_TESTS, {"type": "parallel", "steps": {}})
        steps[KEY_UNIT_TESTS].setdefault("steps", {}).update(unit_test_steps)

        clone_steps = self._collect_git_clone_steps(project)
        if clone_steps:
            steps.setdefault(KEY_CLONE_DEPENDENCIES, {"type": "parallel", "steps": {}})
            steps[KEY_CLONE_DEPENDENCIES].setdefault("steps", {}).update(clone_steps)

        # MISSING: `version`/`stages` pipeline scaffolding (present when the
        # template itself declares them, not computed here), the
        # prepare_deployment/deploy steps (entirely template-driven already), api/
        # e2e test steps and their environment/URL wiring, secrets/db-connect-string/
        # registry-secret wiring into the deployment step's arguments, rollout-wait
        # commands, and parallel-step batching + stage ordering (sort_parallel_steps/
        # order_steps_by_stage in legacy) - none of that is reproduced here yet.

        if write_on_disk:
            self.write(base, output_path=output_path)

        return base
