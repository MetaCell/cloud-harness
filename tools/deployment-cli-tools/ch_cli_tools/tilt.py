"""Generates a Tiltfile from a CHProject.

Actual deployment logic is delegated to a project-supplied, static
deployment-configuration/tilt-deploy.ext (Starlark, never generated) - this
generator's job is narrower: describe what to build (docker_build calls) and
how to link each deployed app's Tilt UI (k8s_resource/cmd_button), the same
build-artifact data CHSkaffold already assembles, reshaped for Tilt instead
of skaffold.yaml.

CHTilt.generate() algorithm:
1. Every base/common image in the project (CHProject.base_images - already
   unconditional, not dependency-scoped, matching legacy's own breadth here)
   gets a build artifact.
2. Every involved app that's buildable gets one too, plus every one of its
   tasks unconditionally (own_build_args only applies to the app itself, not
   its tasks, matching legacy).
3. Any further transitive build dependency not already covered gets pulled
   in the same way CHSkaffold does.
4. is_app is whether the app's harness.service.auto is set (matches legacy
   exactly, not harness.deployment.auto - these are independent flags in the
   schema); its Tilt UI link uses the app's subdomain (display only). Tasks
   carry their owning app's real name as parent_app_name, matched against
   that same stable key (app_key) in the template - legacy itself matched
   against the parent's subdomain-swapped display name there, which silently
   breaks the task/parent link whenever an app's subdomain differs from its
   own name; fixed here instead of reproduced, since this file was already
   being copied into ng's own territory rather than merely referenced.
"""

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .model import CHValues, register_file
from .skaffold import _CLONE_SH
from .utils import resolve_path  # type: ignore

_env = Environment(
    loader=PackageLoader(package_name="ch_cli_tools", package_path="templates/tilt"),
    autoescape=select_autoescape(),
)


@register_file("tilt", lambda root: root / "Tiltfile")
class CHTilt(CHValues):
    def qualify(self, image_name):
        return self.project.qualify(image_name)

    def _context_for(self, entity):
        return entity.dockerfile.resolve_context(self.path.parent).resolve_for_build(
            self.path.parent
        )

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

    def _build_args(self, dependencies, own_build_args=None):
        args = {}
        if self.project.config.local or self.project.config.debug:
            args["DEBUG"] = "true"
        for dep in dependencies:
            if isinstance(dep, str):
                continue
            args[dep.name.replace("-", "_").upper()] = self.qualify(dep.image_name)
        if own_build_args:
            args.update(own_build_args)
        args.update(self.project.all_source_images())
        return args

    def _artifact(
        self,
        entity,
        *,
        is_app=False,
        is_task=False,
        parent_app_name=None,
        name=None,
        own_build_args=None,
    ):
        context = self._context_for(entity)
        dependencies = self.project._combined_dependencies(entity)
        artifact = {
            "name": name or entity.name,
            "app_key": entity.name,
            "image": self.qualify(entity.image_name),
            "context": str(context.path),
            "is_app": is_app,
            "is_task": is_task,
            "parent_app_name": parent_app_name,
            "docker": {
                "dockerfile": str(context.dockerfile.path),
                "buildArgs": self._build_args(dependencies, own_build_args),
            },
        }
        if hasattr(entity, "git_dependencies"):
            hooks = self._collect_git_clone_hooks(entity, context.path)
            if hooks:
                artifact["hooks"] = hooks
        return artifact

    def _collect_artifacts(self) -> dict:
        project = self.project
        artifacts = {}

        for base_image in project.base_images.values():
            if not base_image.dockerfile.exists():
                continue
            artifacts[base_image.name] = self._artifact(base_image)

        for app in project.involved_apps:
            if isinstance(app, str):
                continue

            if app.dockerfile.exists() and not app.deployment_config.get("image"):
                is_app = bool(resolve_path(app.harness_config, "service.auto"))
                subdomain = resolve_path(app.harness_config, "subdomain")
                artifacts[app.name] = self._artifact(
                    app,
                    is_app=is_app,
                    name=subdomain or app.name,
                    own_build_args=app.build_args,
                )

            for task in app.tasks.values():
                if not task.dockerfile.exists():
                    continue
                artifacts[task.name] = self._artifact(
                    task, is_task=True, parent_app_name=app.name
                )

        for dependency in project.all_build_dependencies(set(artifacts)).values():
            if isinstance(dependency, str) or dependency.name in artifacts:
                continue
            artifacts[dependency.name] = self._artifact(dependency)

        return artifacts

    def generate(self, write_on_disk=True, output_path=".") -> str:
        project = self.project
        artifacts = self._collect_artifacts()
        images = list(artifacts.values())
        apps = [a for a in images if a["is_app"]]

        config = project.config
        tiltfile = _env.get_template("tilt-template.tpl").render(
            ch_root=str(project.all_layers()[-1].root),
            name=config.namespace or "",
            namespace=config.namespace or "",
            domain=config.domain,
            images=images,
            apps=apps,
        )

        if write_on_disk:
            self.write(tiltfile, output_path=output_path)

        return tiltfile

    def write(self, base, output_path=None) -> None:
        if output_path is None:
            target = self.path
        else:
            target = Path(output_path) / self.path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(base)
