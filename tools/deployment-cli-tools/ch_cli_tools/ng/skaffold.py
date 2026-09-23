from functools import lru_cache

from .model import CHValues, register_file


@register_file(
    "skaffold_template",
    lambda root: root / "deployment-configuration" / "skaffold-template.yaml",
)
class CHSkaffoldTemplate(CHValues):
    @lru_cache
    def all_values(self):
        project = self.project
        default = project.ch_skaffold_template
        layer = project.skaffold_template
        layer.env = "project"
        return default.merge_with(layer)


@register_file("skaffold", lambda root: root / "skaffold.yaml")
class CHSkaffold(CHValues):
    def generate(self, write_on_disk=True):
        project = self.project

        base = project.skaffold_template.all_values()

        artifacts = []
        task_image_overrides = {}
        app_image_overrides = {}

        for app in project.involved_apps:
            if isinstance(app, str):
                # MISSING: unresolved dependency name (not a scanned CHApp) - nothing to
                # build a Dockerfile artifact from without further app metadata.
                continue

            if app.dockerfile.path.exists():
                artifact = {
                    "image": app.image_name,
                    "context": str(
                        app.path.resolve().relative_to(
                            self.path.parent.resolve(), walk_up=True
                        )
                    ),
                    "docker": {"dockerfile": app.dockerfile.path.name},
                }

                requires = []
                for dep in app.build_dependencies():
                    if isinstance(dep, str):
                        # MISSING: base-image / task-image build dependencies (e.g.
                        # "cloudharness-flask") aren't scanned apps, so they can't be
                        # resolved to a `requires` artifact reference here.
                        continue
                    requires.append(
                        {
                            "image": dep.image_name,
                            "alias": dep.name.replace("-", "_").upper(),
                        }
                    )
                if requires:
                    artifact["requires"] = requires

                # MISSING: env-specific dockerfile selection (<env>.Dockerfile), build
                # args (DEBUG flag, harness.dockerfile.build_args, source_images), ssh
                # config, and git-dependency clone hooks - none of these are exposed by
                # CHApp/CHDockerfile yet.
                artifacts.append(artifact)
                app_image_overrides[app.name] = app.image_name

            for task in app.tasks.values():
                if not task.dockerfile.path.exists():
                    continue
                artifacts.append(
                    {
                        "image": task.image_name,
                        "context": str(
                            task.path.resolve().relative_to(
                                self.path.parent.resolve(), walk_up=True
                            )
                        ),
                        "docker": {"dockerfile": task.dockerfile.path.name},
                    }
                )
                task_image_overrides[task.name] = task.image_name

        # MISSING: infrastructure/base-images and infrastructure/common-images (static
        # images) aren't scanned by CHProject at all - only applications/*/ - so those
        # artifacts can't be produced here.

        build = base.setdefault("build", {})
        build["artifacts"] = artifacts
        # MISSING: tag policy depends on registry/tag/local config, none of which exists
        # yet on CHProject/CHDeployConfig - defaulting to content-hash tagging like the
        # old "no explicit tag, not local" fallback. Checked for falsy, not just
        # absent: the default skaffold-template.yaml already ships an empty
        # `build.tagPolicy: {}`, so a plain `setdefault` would never fire.
        if not build.get("tagPolicy"):
            build["tagPolicy"] = {"sha256": {}}

        deploy = base.setdefault("deploy", {})
        releases = deploy.setdefault("helm", {}).setdefault("releases", [{}])
        release_config = releases[0]
        # MISSING: no `namespace` on CHProject/CHDeployConfig yet - old code set both
        # `name` and `namespace` on the release from helm_values.namespace.
        overrides = release_config.setdefault("artifactOverrides", {})
        overrides["apps"] = {
            name: {"harness": {"deployment": {"image": image}}}
            for name, image in app_image_overrides.items()
        }
        overrides["task-images"] = task_image_overrides
        # MISSING: `overrides.apps` (command/args override for gunicorn-based task
        # entrypoints) and `test` (per-app unit test commands from harness.test.unit)
        # aren't modeled by CHApp yet either.

        # MISSING: docker-compose backend (KEY_APPS/COMPOSE_ENGINE branch) isn't modeled
        # - CHDeployConfig has no flag for it, so this always emits a helm deploy block.

        if write_on_disk:
            self.write(base)

        return base
