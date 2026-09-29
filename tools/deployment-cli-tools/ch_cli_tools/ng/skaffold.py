from functools import lru_cache
from pathlib import Path

from .model import CHBaseImage, CHValues, register_file

# tools/clone.sh, shipped alongside this package - not part of any deployed
# project, so it's located relative to this file, not project.root/ch_path.
_CLONE_SH = Path(__file__).resolve().parent.parent.parent.parent / "clone.sh"


@register_file(
    "skaffold_template",
    lambda root: root / "deployment-configuration" / "skaffold-template.yaml",
)
class CHSkaffoldTemplate(CHValues):
    def __init__(self, path, parent, env=None):
        super().__init__(path, parent, env or "project")
        self.default = CHValues(
            self.project.ch_path
            / "deployment-configuration"
            / "skaffold-template.yaml",
            self.project,
        )

    @lru_cache
    def all_values(self):
        return self.default.merge_with(self)


@register_file("skaffold", lambda root: root / "skaffold.yaml")
class CHSkaffold(CHValues):
    def qualify(self, image_name):
        registry = self.project.config.registry
        if registry and not registry.endswith("/"):
            registry = f"{registry}/"
        return f"{registry}{image_name}"

    def _build_docker_options(self, dockerfile_path, own_build_args=None):
        args = dict(self.project.all_source_images())
        if own_build_args:
            args.update(own_build_args)
        if self.project.config.local or self.project.config.debug:
            args["DEBUG"] = "true"

        options = {"dockerfile": str(dockerfile_path), "ssh": "default"}
        if args:
            options["buildArgs"] = args
        return options

    def _collect_app_dockerfile_artifact(self, app):
        context = app.dockerfile.resolve_context(self.path.parent)
        artifact = {
            "image": self.qualify(app.image_name),
            "context": str(context.path),
            "docker": self._build_docker_options(
                context.dockerfile.path, app.build_args
            ),
        }

        requires = []
        for dep in app.build_dependencies():
            if isinstance(dep, str):
                # A build dependency that doesn't match a scanned app,
                # infrastructure/base-images/, or infrastructure/common-images/
                # entry - genuinely unresolvable (e.g. a typo), not a scanning gap.
                continue
            requires.append(
                {
                    "image": self.qualify(dep.image_name),
                    "alias": dep.name.replace("-", "_").upper(),
                }
            )
        if requires:
            artifact["requires"] = requires

        hooks = self._collect_git_clone_hooks(app, context.path)
        if hooks:
            artifact["hooks"] = hooks

        return artifact, artifact["image"]

    def _collect_git_clone_hooks(self, app, context_path):
        git_deps = app.git_dependencies
        if not git_deps:
            return None

        before = []
        for dep in git_deps:
            url = dep["url"]
            repo_name = Path(url).name.split(".")[0]
            clone_dir = context_path / "dependencies"
            if dep.get("path"):
                clone_dir = clone_dir / dep["path"]
            clone_dir = clone_dir / repo_name
            before.append(
                {
                    "command": [
                        "sh",
                        str(_CLONE_SH),
                        dep.get("branch_tag"),
                        url,
                        str(clone_dir),
                    ]
                }
            )
        return {"before": before}

    def _collect_build_dependency_artifact(self, dependency):
        context = dependency.dockerfile.resolve_context(self.path.parent)
        return {
            "image": self.qualify(dependency.image_name),
            "context": str(context.path),
            "docker": self._build_docker_options(context.dockerfile.path),
        }

    def _collect_task_dockerfile_artifacts(self, app):
        artifacts = []
        overrides = {}
        for task in app.tasks.values():
            if not task.dockerfile.path.exists():
                continue
            context = task.dockerfile.resolve_context(self.path.parent)
            artifact = {
                "image": self.qualify(task.image_name),
                "context": str(context.path),
                "docker": self._build_docker_options(context.dockerfile.path),
            }
            artifacts.append(artifact)
            overrides[task.name] = artifact["image"]
        return artifacts, overrides

    def _collect_entrypoint_override(self, app):
        entrypoint = app.app_entrypoint
        if entrypoint is None:
            return None
        return {
            "harness": {
                "deployment": {
                    "command": ["python"],
                    "args": [f"/usr/src/app/{entrypoint.name}/__main__.py"],
                }
            }
        }

    def _collect_test_entry(self, app):
        commands = app.unit_test_commands
        if not commands:
            return None
        return {
            "image": self.qualify(app.image_name),
            "custom": [{"command": f"docker run $IMAGE {cmd}"} for cmd in commands],
        }

    def _collect_app_and_task_artifacts(self):
        artifacts = []
        app_image_overrides = {}
        task_image_overrides = {}
        entrypoint_overrides = {}
        test_entries = []

        for app in self.project.involved_apps:
            if isinstance(app, str):
                continue

            if app.dockerfile.exists():
                artifact, image = self._collect_app_dockerfile_artifact(app)
                artifacts.append(artifact)
                app_image_overrides[app.name] = image

                entrypoint_override = self._collect_entrypoint_override(app)
                if entrypoint_override is not None:
                    entrypoint_overrides[app.name] = entrypoint_override

                test_entry = self._collect_test_entry(app)
                if test_entry is not None:
                    test_entries.append(test_entry)

            task_artifacts, task_overrides = self._collect_task_dockerfile_artifacts(
                app
            )
            artifacts.extend(task_artifacts)
            task_image_overrides.update(task_overrides)

        return (
            artifacts,
            app_image_overrides,
            task_image_overrides,
            entrypoint_overrides,
            test_entries,
        )

    def _collect_build_dependency_artifacts(self):
        build_dependencies_needed = {}
        for app in self.project.involved_apps:
            if isinstance(app, str):
                # skipping unresolved apps
                continue
            for dep in app.build_dependencies():
                if isinstance(dep, str):
                    # skipping unresolved build dependencies
                    continue
                build_dependencies_needed[dep.name] = dep
        return [
            self._collect_build_dependency_artifact(dependency)
            for dependency in build_dependencies_needed.values()
        ]

    def generate(self, write_on_disk=True):
        project = self.project

        base = project.skaffold_template.all_values()

        (
            artifacts,
            app_image_overrides,
            task_image_overrides,
            entrypoint_overrides,
            test_entries,
        ) = self._collect_app_and_task_artifacts()
        artifacts.extend(self._collect_build_dependency_artifacts())

        if test_entries:
            base["test"] = test_entries

        build = base.setdefault("build", {})
        build["artifacts"] = artifacts
        # An explicit external tag (e.g. from CI) that isn't a local build, or a
        # docker-compose deploy, both need skaffold to trust the tag it's handed
        # rather than compute its own content hash - mirrors the old
        # create_skaffold_configuration()'s tagPolicy branch.
        if project.config.backend == "compose" or (
            project.config.tag and not project.config.local
        ):
            build["tagPolicy"] = {"envTemplate": {"template": '"{{.TAG}}"'}}
        elif not build.get("tagPolicy"):
            # Checked for falsy, not just absent: the default skaffold-template.yaml
            # already ships an empty `build.tagPolicy: {}`, so a plain `setdefault`
            # would never fire.
            build["tagPolicy"] = {"sha256": {}}

        if project.config.backend == "compose":
            base["deploy"] = {
                "docker": {
                    "useCompose": True,
                    "images": [a["image"] for a in artifacts if a.get("image")],
                }
            }
        else:
            deploy = base.setdefault("deploy", {})
            releases = deploy.setdefault("helm", {}).setdefault("releases", [{}])
            release_config = releases[0]
            if project.config.namespace:
                release_config["name"] = project.config.namespace
                release_config["namespace"] = project.config.namespace
            artifact_overrides = release_config.setdefault("artifactOverrides", {})
            artifact_overrides["apps"] = {
                name: {"harness": {"deployment": {"image": image}}}
                for name, image in app_image_overrides.items()
            }
            artifact_overrides["task-images"] = task_image_overrides

            if entrypoint_overrides:
                release_config.setdefault("overrides", {})["apps"] = (
                    entrypoint_overrides
                )

        if write_on_disk:
            self.write(base)

        return base
