"""deployment-configuration/compose/ is a parallel Helm chart (its own
Chart.yaml/values.yaml/templates/), rendered through the real `helm` binary
used purely as a Go-template engine - `helm template` never talks to a
cluster here. Everything about which apps/images/values go into it is
identical to the real Helm chart (CHProject.build_final_helm_values()).
"""

import shutil
import subprocess
from pathlib import Path

from .helm import CHHelmChart
from .model import CHAppInstance, CHValues, register_file
from .utils import (  # type: ignore
    _merge_base_chain,
    collect_and_merge_env_specific_files,
    get_yaml_parser,
)


def _merge_helper_templates(
    app, destination: Path, templates_dir_of=lambda a: a.path / "deploy" / "templates"
) -> None:
    if app.base is not None:
        _merge_helper_templates(app.base, destination, templates_dir_of)
    templates_dir = templates_dir_of(app)
    if not templates_dir.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for helper in templates_dir.glob("_*.tpl"):
        dest_file = destination / helper.name
        if not dest_file.exists():
            shutil.copy(helper, dest_file)


@register_file(
    "docker_compose",
    lambda root: root / "deployment-configuration" / "compose" / "Chart.yaml",
)
class CHDockerCompose(CHHelmChart):
    def generate(self) -> None:
        project = self.project
        dest = Path(project.config.output_path) / "compose"
        shutil.rmtree(dest, ignore_errors=True)
        _merge_base_chain(
            project, lambda p: p.root / "deployment-configuration" / "compose", dest
        )
        self.write(dest)
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            if isinstance(app, CHAppInstance):
                self._collect_instance_deploy_directories(app, dest)
                continue
            _merge_base_chain(
                app,
                lambda a: a.path / "deploy" / "templates-compose",
                dest / "templates" / app.name,
            )
            _merge_helper_templates(app, dest / "templates" / app.name)
            _merge_base_chain(
                app,
                lambda a: a.path / "deploy" / "resources",
                dest / "resources" / app.name,
            )
        collect_and_merge_env_specific_files(dest, project.config.envs)

        values = project.build_final_helm_values(write_on_disk=False).to_dict()
        CHValues.write_on_disk(dest / "values.yaml", values)
        CHValues.write_on_disk(dest / "allvalues.yaml", self._secrets_stripped(values))

        self._render(dest)

    def _collect_instance_deploy_directories(self, instance: CHAppInstance, dest: Path) -> None:
        parent, own = instance.parent_app, instance.instance_name
        destination = dest / "templates" / instance.name
        _merge_base_chain(
            parent, lambda a: a.path / "deploy" / "templates-compose", destination
        )
        _merge_helper_templates(parent, destination)
        _merge_base_chain(
            parent,
            lambda a, own=own: a.path / "deploy" / "instances" / own / "templates-compose",
            destination,
        )
        _merge_helper_templates(
            parent,
            destination,
            lambda a, own=own: a.path / "deploy" / "instances" / own / "templates",
        )
        _merge_base_chain(
            parent, lambda a: a.path / "deploy" / "resources", dest / "resources" / instance.name
        )
        _merge_base_chain(
            parent,
            lambda a, own=own: a.path / "deploy" / "instances" / own / "resources",
            dest / "resources" / instance.name,
        )

    def _secrets_stripped(self, values: dict) -> dict:
        apps = {
            name: {**app, "harness": {**app["harness"], "secrets": {}}}
            for name, app in values["apps"].items()
        }
        return {**values, "apps": apps}

    def _render(self, dest: Path) -> None:
        rendered = subprocess.run(
            ["helm", "template", str(dest)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        yaml = get_yaml_parser()
        main_document = None
        for document in yaml.load_all(rendered):
            if not document:
                continue
            metadata = document.get("cloudharness-metadata")
            if metadata:
                embedded_path = dest / metadata["path"]
                embedded_path.parent.mkdir(parents=True, exist_ok=True)
                embedded_path.write_text(document["data"])
            else:
                main_document = document

        compose_path = dest.parent.parent / "docker-compose.yaml"
        with compose_path.open("w", encoding="utf-8") as f:
            yaml.dump(main_document, f)
