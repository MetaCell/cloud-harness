import shutil
from pathlib import Path

from .model import CHAppInstance, CHValues, register_file
from .utils import (  # type: ignore
    _merge_base_chain,
    collect_and_merge_env_specific_files,
    dict_merge,
)


@register_file(
    "helm_chart",
    lambda root: root / "deployment-configuration" / "helm" / "Chart.yaml",
)
class CHHelmChart(CHValues):
    def overrides(self) -> dict:
        config = self.project.config
        metadata = {}
        if config.chart_name:
            metadata["name"] = config.chart_name
        if config.namespace:
            metadata["metadata"] = {"namespace": config.namespace}
        if config.chart_version:
            metadata["version"] = config.chart_version
        if config.app_version:
            metadata["appVersion"] = config.app_version
        return metadata

    def write(self, output_path=None) -> None:
        overrides = self.overrides()
        if not overrides:
            return
        chart = dict_merge(self.merge_with_base_and_envs(), overrides)
        super().write(chart, output_path=output_path)

    def generate(self) -> None:
        project = self.project
        dest = Path(project.config.output_path) / "helm"
        shutil.rmtree(dest, ignore_errors=True)
        _merge_base_chain(
            project, lambda p: p.root / "deployment-configuration" / "helm", dest
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
                lambda a: a.path / "deploy" / "templates",
                dest / "templates" / app.name,
            )
            _merge_base_chain(
                app,
                lambda a: a.path / "deploy" / "resources",
                dest / "resources" / app.name,
            )
            _merge_base_chain(
                app, lambda a: a.path / "deploy" / "charts", dest / "charts" / app.name
            )
        collect_and_merge_env_specific_files(dest, project.config.envs)

    def _collect_instance_deploy_directories(self, instance: CHAppInstance, dest: Path) -> None:
        parent, own = instance.parent_app, instance.instance_name
        for kind in ("templates", "resources", "charts"):
            _merge_base_chain(
                parent, lambda a, kind=kind: a.path / "deploy" / kind, dest / kind / instance.name
            )
            _merge_base_chain(
                parent,
                lambda a, kind=kind: a.path / "deploy" / "instances" / own / kind,
                dest / kind / instance.name,
            )
