"""Generates skaffold.yaml from a CHProject.

`skaffold dev`/`skaffold run` is what actually builds every image a CH deployment needs and hands their freshly-built tags to Helm, but it needs a build+deploy plan to do that - and that plan can't be hand-maintained.
A CH project is a monorepo of independently-versioned apps/tasks/base-images, only some of which are deployed on any given run (--include/--exclude, per-env config), each of which may depend on another one being built first (an app's Dockerfile FROM-ing a base image, or an app declaring another app/task as a build prerequisite).
Generation derives, from the project's actual structure, exactly which images need building, in what order, with what build args and per-env Dockerfile variant, and how each one maps onto the Helm values so the deployed pod gets the image that was just built rather than a stale one.

CH model concepts this relies on:
- CHProject.involved_apps (the soft/hard dependency closure over entrypoint
  apps) scopes artifacts to what's actually deployed, not every app in the
  repo.
- CHApp/CHAppTask/CHBaseImage's `.dockerfile`/`.image_name`/`.build_context`
  are the raw facts needed to build: path, image name, context directory.
  `.dockerfile` also resolves a Dockerfile nested under a conventional
  subdirectory (`server`/`src`/`backend`), not just the entity's own top
  level - several real apps build this way.
- CHDockerfile.resolved/.resolve_context give env-aware Dockerfile selection
  (an `<env>.Dockerfile` override) and context-relative pathing.
- app.build_dependencies() (explicit `dependencies.build`) and
  CHDockerfile.base_dependencies (guessed from the Dockerfile's own FROM/ARG
  chain) together give the real build-ordering graph (`requires:`), since a
  build dependency can be declared explicitly or only exist implicitly in the
  Dockerfile itself.
- app.deployment_config (`harness.deployment.image`) tells apart an app with
  a prebuilt/external image (never built here) from one CH must build.
- app.git_dependencies are external repos that must be cloned before the
  build can run, wired in as pre-build hooks.
- app.app_entrypoint/app.test.unit.commands are the deployment command/args
  overrides and unit-test wiring that skaffold.yaml also carries.
- CHProject.all_source_images() is a project-wide aggregation of
  ARG-defaulted base images, so every artifact gets the pinned versions as
  build args.
- CHDeployConfig (registry/tag/local/debug/namespace/backend/
  manage_task_images) holds the deployment-target knobs: image qualification,
  tag policy, compose vs helm, namespace, and whether a task whose own owning
  app isn't itself deployed still gets built when something else needs it.

CHSkaffold.generate() algorithm:

1. Start from the merged skaffold-template.yaml (CH default + project
   override).
2. For every involved app (the project's soft/hard dependency closure),
   unless it declares a prebuilt harness.deployment.image, build an artifact
   for its own Dockerfile: context, dockerfile path (env-Dockerfile aware),
   buildArgs (project-wide source_images + the app's own
   harness.dockerfile.buildArgs), ssh passthrough, git-dependency clone
   hooks, an entrypoint override (gunicorn/Django detection) and a
   unit-test entry, if any apply.
3. Every task under an involved app gets its own artifact unconditionally,
   whether or not the app itself builds.
4. Each artifact's `requires:` comes from combining that app/task's
   explicit dependencies.build with its Dockerfile's guessed FROM/ARG chain
   (base_dependencies), deduplicated and validated - an unresolved
   *explicit* build dependency raises.
5. Any base image, app or task that's a build dependency of something above
   but isn't already covered by an app/task artifact is pulled in
   transitively (its own build dependencies are followed too) and given
   its own artifact, so build.artifacts never omits something the graph
   actually needs - except a task whose own owning app isn't itself
   deployed, when manage_task_images is False: that one (and anything only
   reachable through it) is dropped instead, regardless of what needs it.
6. tagPolicy is envTemplate for compose or an explicit external tag, sha256
   content-hash otherwise.
7. The deploy block is either a compose block (useCompose + image list) or
   a helm block with per-app/task image overrides and entrypoint
   overrides.
"""

from functools import lru_cache
from pathlib import Path

from .model import CHValues, register_file
from .utils import dict_merge  # type: ignore

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

    @lru_cache
    def all_values(self):
        own = self.all_raw_values() if self.exists() else {}
        base = self.containing_project.base
        if base is None:
            return own
        return dict_merge(base.skaffold_template.all_values(), own)


@register_file("skaffold", lambda root: root / "skaffold.yaml")
class CHSkaffold(CHValues):
    def qualify(self, image_name):
        return self.project.qualify(image_name)

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

    def _collect_requires(self, deps):
        requires = []
        seen = set()
        for dep in deps:
            if isinstance(dep, str):
                continue
            if dep.name in seen:
                continue
            seen.add(dep.name)
            requires.append(
                {
                    "image": self.qualify(dep.image_name),
                    "alias": dep.name.replace("-", "_").upper(),
                }
            )
        return requires

    def _requires_for(self, entity):
        return self._collect_requires(self.project._combined_dependencies(entity))

    def _context_for(self, entity):
        return entity.dockerfile.resolve_context(self.path.parent).resolve_for_build(
            self.path.parent
        )

    def _collect_app_dockerfile_artifact(self, app):
        context = self._context_for(app)
        artifact = {
            "image": self.qualify(app.image_name),
            "context": str(context.path),
            "docker": self._build_docker_options(
                context.dockerfile.path, app.build_args
            ),
        }

        requires = self._requires_for(app)
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
        context = self._context_for(dependency)
        artifact = {
            "image": self.qualify(dependency.image_name),
            "context": str(context.path),
            "docker": self._build_docker_options(context.dockerfile.path),
        }
        requires = self._requires_for(dependency)
        if requires:
            artifact["requires"] = requires
        return artifact

    def _collect_task_dockerfile_artifacts(self, app):
        artifacts = []
        overrides = {}
        for task in app.tasks.values():
            if not task.dockerfile.path.exists():
                continue
            context = self._context_for(task)
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
        commands = app.test.unit.commands
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

            if app.dockerfile.exists() and not app.deployment_config.get("image"):
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

    def _collect_build_dependency_artifacts(self, already_covered):
        return [
            self._collect_build_dependency_artifact(dependency)
            for dependency in self.project.all_build_dependencies(
                already_covered
            ).values()
        ]

    def generate(self, write_on_disk=True, output_path="."):
        project = self.project

        base = project.skaffold_template.all_values()

        (
            artifacts,
            app_image_overrides,
            task_image_overrides,
            entrypoint_overrides,
            test_entries,
        ) = self._collect_app_and_task_artifacts()
        artifacts.extend(
            self._collect_build_dependency_artifacts(
                {*app_image_overrides.keys(), *task_image_overrides.keys()}
            )
        )

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

            release_config.setdefault("overrides", {})["apps"] = entrypoint_overrides

        if write_on_disk:
            self.write(base, output_path=output_path)

        return base
