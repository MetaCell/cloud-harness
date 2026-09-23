from functools import lru_cache

from .model import CHValues, register_file
from .utils import dict_merge  # type: ignore


@register_file(
    "codefresh_template",
    lambda root: root / "deployment-configuration" / "codefresh-template.yaml",
)
class CHCodefreshTemplate(CHValues):
    @lru_cache
    def all_values(self):
        project = self.project
        default = CHValues(
            project.ch_path / "deployment-configuration" / "codefresh-template.yaml",
            project,
        )
        return dict_merge(
            default.merge_with(default.for_env(project.config.env)),
            self.merge_with(self.for_env(project.config.env)),
        )


@register_file(
    "codefresh", lambda root: root / "deployment" / "codefresh.yaml", only_env=True
)
class CHCodefresh(CHValues):
    def qualify(self, image_name):
        registry = self.project.config.registry
        if registry and not registry.endswith("/"):
            registry = f"{registry}/"
        return f"{registry}{image_name}"

    def _collect_app_build_step(self, app):
        step = {
            "title": f"Building {app.name}",
            "type": "build",
            "image_name": self.qualify(app.image_name),
            "working_directory": str(
                app.path.resolve().relative_to(self.path.parent.resolve(), walk_up=True)
            ),
            "dockerfile": app.dockerfile.path.name,
            "tag": "${{CF_SHORT_REVISION}}",
        }
        if self.project.config.local or self.project.config.debug:
            step["build_arguments"] = ["DEBUG=true"]
        # MISSING: env-specific dockerfile selection, the rest of build args beyond
        # DEBUG, git-dependency clone steps, and a `stage:` assignment (no `stages`
        # pipeline scaffolding is modeled here) - none of these are exposed by
        # CHApp/CHDockerfile yet. `registry_secret_name`/`domain` are on
        # CHDeployConfig now but have nothing to plug into yet either: registry auth
        # for a push is a Codefresh registry integration reference, not a k8s secret
        # name (that's a Helm-values concern, a generator we haven't built), and
        # `domain` only matters for e2e test steps, which aren't generated at all.
        return f"build_{app.name.replace('-', '_')}", step

    def _collect_task_build_steps(self, app):
        steps = {}
        for task in app.tasks.values():
            if not task.dockerfile.path.exists():
                continue
            steps[f"build_{task.name.replace('-', '_')}"] = {
                "title": f"Building {task.name}",
                "type": "build",
                "image_name": self.qualify(task.image_name),
                "working_directory": str(
                    task.path.resolve().relative_to(
                        self.path.parent.resolve(), walk_up=True
                    )
                ),
                "dockerfile": task.dockerfile.path.name,
                "tag": "${{CF_SHORT_REVISION}}",
            }
        return steps

    def generate(self, write_on_disk=True):
        project = self.project

        base = project.codefresh_template.all_values()

        build_steps = {}

        for app in project.involved_apps:
            if isinstance(app, str):
                continue

            if app.dockerfile.path.exists():
                key, step = self._collect_app_build_step(app)
                build_steps[key] = step

            build_steps.update(self._collect_task_build_steps(app))

        # MISSING: infrastructure/base-images and infrastructure/common-images
        # (static images) aren't scanned by CHProject at all - only applications/*/ -
        # so those steps can't be produced here, unlike the old
        # codefresh_steps_from_base_path() passes over BASE_IMAGES_PATH/
        # STATIC_IMAGES_PATH.

        steps = base.setdefault("steps", {})
        steps.update(build_steps)

        # MISSING: `version`/`stages` pipeline scaffolding, the git-clone/
        # prepare_deployment/deploy steps, e2e test environment wiring, and unit
        # test steps (harness.test.unit) all came from the old
        # codefresh-template.yaml + create_codefresh_deployment_scripts()'s own
        # logic - none of that is reproduced here, only the per-app/task build steps.

        if write_on_disk:
            self.write(base)

        return base
