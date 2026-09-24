from functools import lru_cache

from .model import CHBaseImage, CHValues, register_file


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

    def _collect_app_dockerfile_artifact(self, app):
        context = app.dockerfile.resolve_context(self.path.parent)
        artifact = {
            "image": self.qualify(app.image_name),
            "context": str(context.path),
            "docker": {"dockerfile": str(context.dockerfile.path)},
        }
        if self.project.config.local or self.project.config.debug:
            artifact["docker"]["buildArgs"] = {"DEBUG": "true"}

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

        # MISSING: env-specific dockerfile selection (<env>.Dockerfile), the rest of
        # build args beyond DEBUG (harness.dockerfile.build_args, source_images), ssh
        # config, and git-dependency clone hooks - none of these are exposed by
        # CHApp/CHDockerfile yet.
        return artifact, artifact["image"]

    def _collect_build_dependency_artifact(self, dependency):
        context = dependency.dockerfile.resolve_context(self.path.parent)
        return {
            "image": self.qualify(dependency.image_name),
            "context": str(context.path),
            "docker": {"dockerfile": str(context.dockerfile.path)},
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
                "docker": {"dockerfile": str(context.dockerfile.path)},
            }
            artifacts.append(artifact)
            overrides[task.name] = artifact["image"]
        return artifacts, overrides

    def _collect_app_and_task_artifacts(self):
        artifacts = []
        app_image_overrides = {}
        task_image_overrides = {}

        for app in self.project.involved_apps:
            if isinstance(app, str):
                continue

            if app.dockerfile.path.exists():
                artifact, image = self._collect_app_dockerfile_artifact(app)
                artifacts.append(artifact)
                app_image_overrides[app.name] = image

            task_artifacts, task_overrides = self._collect_task_dockerfile_artifacts(
                app
            )
            artifacts.extend(task_artifacts)
            task_image_overrides.update(task_overrides)

        return artifacts, app_image_overrides, task_image_overrides

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

        artifacts, app_image_overrides, task_image_overrides = (
            self._collect_app_and_task_artifacts()
        )
        artifacts.extend(self._collect_build_dependency_artifacts())

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
            overrides = release_config.setdefault("artifactOverrides", {})
            overrides["apps"] = {
                name: {"harness": {"deployment": {"image": image}}}
                for name, image in app_image_overrides.items()
            }
            overrides["task-images"] = task_image_overrides
            # MISSING: `overrides.apps` (command/args override for gunicorn-based task
            # entrypoints) and `test` (per-app unit test commands from
            # harness.test.unit) aren't modeled by CHApp yet either.

        if write_on_disk:
            self.write(base)

        return base
