"""Generates .vscode/launch.json (the Cloud Code Kubernetes debug config)
from a CHProject's already-built HarnessMainConfig.

Unlike every other generator here, this file isn't a deployment artifact -
it's a local IDE convenience that lives at the repo root (wherever VS Code's
`${workspaceFolder}` is, i.e. the current working directory when generation
runs), independent of config.output_path. Regeneration must be idempotent
against a developer's own hand-edited launch.json: it only ever replaces the
single "CloudHarness: Run/Debug" entry it owns, merged onto whatever other
configurations are already there, never discarding them.

CH model concepts this relies on:
- values.apps also holds every deployed app instance (e.g. "samples-instance1"),
  which CHProject[name]/scanned_apps doesn't know about - resolved instead via
  scanned_apps/all_instances(), same as entrypoint_apps() does. An instance's
  own `.path` is its deploy/instances/<name> override folder, not where its
  backend lives, so its setup.py search uses its parent app's `.path` instead.
- values.apps (the already-built HarnessMainConfig) is the source of both
  which apps are actually deployed and each one's final, qualified image tag
  (harness.deployment.image - populated for every buildable app, not just
  prebuilt ones, by the time build_final_helm_values() returns it).
- app.harness.source_root is the in-container path VS Code should map the
  debugged source tree onto; "/usr/src/app" is the fallback every real
  Dockerfile here actually uses when an app doesn't override it.

CHVSCodeDebug.generate() algorithm:

1. Start from whatever `.vscode/launch.json` already exists in the repo
   (preserving any other hand-written configurations), or an empty
   `{"version": "0.2.0", "configurations": []}` skeleton if there's none yet.
2. Load the merged vscode-debug-template.json (CH default + project
   override, composed across the full project layer chain) - the single
   "CloudHarness: Run/Debug" entry every deployed app's debug target gets
   appended to.
3. Drop any existing configuration with that same name (regenerating
   replaces it wholesale rather than appending duplicates), then add it back
   in, with a freshly-built, empty `debug: []` list.
4. For every deployed app: find its own setup.py (an app's Python backend
   lives nested under a conventional subdirectory, e.g. server/ or
   backend/, not at the app's own top level), and if there's a deployment
   image for it, add a debug entry mapping that source directory (relative
   to the current working directory) onto the container's source_root.
5. Write the whole file back, 2-space indented and key-sorted for a stable
   diff, same as legacy.
"""

import json
from pathlib import Path

from ch_cli_tools.utils import robust_load_json  # type: ignore

from .model import CHAppInstance, CHValues, register_file
from .utils import dict_merge  # type: ignore

_LAUNCH_JSON_DEFAULT = {"version": "0.2.0", "configurations": []}


def _load_json(path: Path) -> dict:
    return robust_load_json(path) if path.exists() else {}


@register_file(
    "vscode_debug_template",
    lambda root: root / "deployment-configuration" / "vscode-debug-template.json",
)
class CHVSCodeDebugTemplate(CHValues):
    def all_raw_values(self) -> dict:
        return _load_json(self.path)

    def all_values(self) -> dict:
        own = self.all_raw_values()
        base = self.containing_project.base
        if base is None:
            return own
        return dict_merge(base.vscode_debug_template.all_values(), own)


@register_file("vscode_debug", lambda root: Path(".vscode/launch.json"))
class CHVSCodeDebug(CHValues):
    def generate(self) -> dict:
        project = self.project
        helm_values = project.build_final_helm_values(write_on_disk=False)
        launch = dict_merge(_LAUNCH_JSON_DEFAULT, _load_json(self.path))
        debug_conf = dict(project.vscode_debug_template.all_values())
        debug_conf["debug"] = []

        launch["configurations"] = [
            conf
            for conf in launch.get("configurations") or []
            if conf.get("name") != debug_conf.get("name")
        ] + [debug_conf]

        for name, app in helm_values.apps.items():
            if not (
                app.harness and app.harness.deployment and app.harness.deployment.image
            ):
                continue
            entity = project.scanned_apps.get(name) or project.all_instances().get(name)
            if entity is None:
                continue
            source_root = (
                entity.parent_app.path if isinstance(entity, CHAppInstance) else entity.path
            )
            setup_py = next(source_root.rglob("setup.py"), None)
            if setup_py is None:
                continue
            source_dir = setup_py.parent
            workspace_path = source_dir.resolve().relative_to(
                Path.cwd().resolve(), walk_up=True
            )
            debug_conf["debug"].append(
                {
                    "image": app.harness.deployment.image,
                    "sourceFileMap": {
                        "justMyCode": False,
                        f"${{workspaceFolder}}/{workspace_path}": (
                            app.harness.source_root or "/usr/src/app"
                        ),
                    },
                }
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(launch, f, indent=2, sort_keys=True)
        return launch
