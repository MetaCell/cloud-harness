import hashlib
import itertools
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

from cloudharness_model import HarnessMainConfig  # type: ignore

KEY_TASK_IMAGES = "task-images"
_ENTRYPOINT_OVERRIDE_PATTERN = re.compile(
    r"CLOUDHARNESS_FLASK|gunicorn|CLOUDHARNESS_DJANGO", re.IGNORECASE
)


from .utils import (
    MERGE_DIRNAME,
    _merge_base_chain,
    collect_and_merge_env_specific_files,
    content_hash,
    dict_merge,  # type: ignore
    env_suffixed_path,
    get_yaml_parser,
    merge_with_layer,
    own_dockerfile_path,
    parse_dockerfile,
    resolve_path,
)


class TaskUnknownError(Exception): ...


class AppUnknownError(Exception): ...


class DependencyUnknownError(Exception): ...


class InvalidVolumeConfigurationError(Exception): ...


class CHUnitTest:
    def __init__(self, config: dict):
        self._config = config

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled"))

    @property
    def commands(self) -> list[str]:
        if not self.enabled:
            return []
        return self._config.get("commands") or []


class CHApiTest:
    def __init__(self, config: dict):
        self._config = config

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled"))

    @property
    def autotest(self) -> bool:
        return bool(self._config.get("autotest"))

    @property
    def run_params(self) -> list[str]:
        return self._config.get("runParams") or []

    @property
    def checks(self) -> list[str]:
        return self._config.get("checks") or []


class CHE2ETest:
    def __init__(self, config: dict):
        self._config = config

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled"))

    @property
    def smoketest(self) -> bool:
        return bool(self._config.get("smoketest"))

    @property
    def ignore_console_errors(self) -> bool:
        return bool(self._config.get("ignoreConsoleErrors"))

    @property
    def ignore_request_errors(self) -> bool:
        return bool(self._config.get("ignoreRequestErrors"))


class CHTest:
    def __init__(self, config: dict):
        self._config = config or {}

    @property
    def unit(self) -> CHUnitTest:
        return CHUnitTest(self._config.get("unit") or {})

    @property
    def api(self) -> CHApiTest:
        return CHApiTest(self._config.get("api") or {})

    @property
    def e2e(self) -> CHE2ETest:
        return CHE2ETest(self._config.get("e2e") or {})


yaml = get_yaml_parser()


class CHApp:
    def __init__(self, path: Path, parent: "CHProject | CHApp"):
        self.path = path
        self.parent = parent
        self.name = self.path.name
        self._dockerfile = CHDockerfile(own_dockerfile_path(self.path), self)
        self.app_basevalues_template = CHValues(
            self.path / "deploy" / "values.yaml", self
        )

    def exists(self):
        return self.path.exists()

    @property
    @lru_cache
    def base(self) -> "CHApp | None":
        lower = self.containing_project.base
        return lower.scanned_apps.get(self.name) if lower is not None else None

    @property
    def dockerfile(self) -> "CHDockerfile":
        own = self._dockerfile.resolved
        if not own.exists() and self.base:
            return self.base.dockerfile
        return own

    @property
    def build_context(self) -> Path:
        return self.path

    def __getitem__(self, key) -> "CHAppTask":
        try:
            return self.tasks[key]
        except KeyError:
            raise TaskUnknownError(f"App {self.name} doesn't own a {key} task")

    @property
    @lru_cache
    def containing_project(self) -> "CHProject":
        project = self.parent
        while isinstance(project, CHApp):
            project = project.parent
        return project

    @property
    def project(self) -> "CHProject":
        return self.containing_project.project

    @lru_cache
    def raw_values(self):
        own = self.app_basevalues_template.merge_with_envs(self.project.config.envs)
        if self.base is None:
            return own
        return dict_merge(self.base.raw_values(), own)

    @lru_cache
    def all_values(self):
        return dict_merge(
            self.project.app_defaults.merge_with_base_and_envs(),
            self.raw_values(),
        )

    @lru_cache
    def _scan_tasks(self) -> dict[str, "CHAppTask"]:
        tasks: dict[str, CHAppTask] = {}
        if self.base is not None:
            for name, task in self.base._scan_tasks().items():
                tasks[name] = CHAppTask(task.path, self)
        for t in self.path.glob("tasks/*/"):
            task = CHAppTask(t, self)
            tasks[task.name] = task
        return tasks

    @property
    @lru_cache
    def tasks(self) -> dict[str, "CHAppTask"]:
        return {
            name: task
            for name, task in self._scan_tasks().items()
            if name not in self.project.config.excludes
        }

    def add_task(self, name):
        self.tasks[name] = CHAppTask(self.path / name, self)

    @property
    @lru_cache
    def templates(self) -> list["CHTemplate"]:
        path = self.path / "deploy" / "templates"
        return [
            CHTemplate(p, self)
            for p in itertools.chain(path.rglob("*.yaml"), path.rglob("*.tpl"))
        ]

    @property
    def manifest(self) -> Path:
        return self.path / ".ch-manifest"

    @property
    def readme(self) -> Path:
        return self.path / "README.md"

    @property
    def harness_config(self):
        return resolve_path(self.all_values(), "harness")

    @property
    def soft_dependencies(self) -> list["CHApp | str"]:
        return [
            self.project.scanned_apps.get(dep, dep)
            for dep in cast(
                list[str],
                resolve_path(self.harness_config, "dependencies.soft", default=[]),
            )
            if dep not in self.project.config.excludes
        ]

    @property
    def hard_dependencies(self) -> list["CHApp | str"]:
        return [
            self.project.scanned_apps.get(dep, dep)
            for dep in cast(
                list[str],
                resolve_path(self.harness_config, "dependencies.hard", default=[]),
            )
            if dep not in self.project.config.excludes
        ]

    def build_dependencies(self) -> list["CHApp | CHBaseImage | CHAppTask | str"]:
        return [
            self.project.scanned_apps.get(dep)
            or self.project.base_images.get(dep)
            or self.project.all_buildable_tasks().get(dep, dep)
            for dep in cast(
                list[str],
                resolve_path(self.harness_config, "dependencies.build", default=[]),
            )
        ]

    @property
    def deployment_config(self):
        return resolve_path(self.harness_config, "deployment", default={})

    @property
    def resources_limits(self):
        return resolve_path(self.deployment_config, "resources.limits", default={})

    @property
    def resources_requests(self):
        return resolve_path(self.deployment_config, "resources.requests", default={})

    @property
    def build_args(self) -> dict[str, str]:
        return resolve_path(self.harness_config, "dockerfile.buildArgs", default={})

    @property
    def test(self) -> CHTest:
        return CHTest(resolve_path(self.harness_config, "test", default={}))

    @property
    def git_dependencies(self) -> list[dict]:
        return resolve_path(self.harness_config, "dependencies.git", default=[]) or []

    @property
    def app_entrypoint(self) -> Path | None:
        candidates = sorted(
            self.build_context.glob("**/__main__.py"), key=lambda p: len(p.parts)
        )
        if not candidates:
            return None

        texts = []
        if self.dockerfile.exists():
            texts.append(self.dockerfile.path.read_text())
        requirements = self.path / "requirements.txt"
        if requirements.exists():
            texts.append(requirements.read_text())

        if not any(_ENTRYPOINT_OVERRIDE_PATTERN.search(text) for text in texts):
            return None
        return candidates[0].parent

    @property
    def image_name(self):
        return f"{self.project.base_image_name()}/{
            resolve_path(
                self.harness_config, 'image_name', default=self.dockerfile.app.name
            )
        }"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name!r} at {hex(id(self))}>"


class CHValues:
    def __init__(
        self,
        path: Path,
        parent: "CHApp | CHProject",
        env: str | None = None,
    ):
        self.app: CHApp | CHProject = parent
        self.path: Path = path
        self.env: str | None = env

    @property
    def project(self):
        return self.app.project

    @property
    def containing_project(self):
        return self.app.containing_project

    @lru_cache
    def all_raw_values(self):
        # Currently only 1 way to parse them as YAML
        # Later would be nice to have a kind of backend to select YAML or other format
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as f:
            return yaml.load(f)

    def exists(self):
        return self.path.exists()

    @classmethod
    def path_for_env(cls, path, env):
        suffix = env if isinstance(env, str) else "-".join(env)
        return env_suffixed_path(path, suffix)

    def for_env(self, env: str | None):
        if env is None:
            return self

        return CHValues(self.path_for_env(self.path, env), self.app, env)

    def merge_with(self, other):
        return merge_with_layer(self, other)

    def merge_with_envs(self, envs: list[str]) -> dict:
        result = self.all_raw_values() if self.exists() else {}
        for env in envs:
            layer = self.for_env(env)
            if layer.exists():
                result = dict_merge(result, layer.all_raw_values())
        return result

    def merge_with_base_and_envs(self) -> dict:
        layer = self.containing_project
        own = self.merge_with_envs(self.project.config.envs)
        if layer.base is None:
            return own
        relative = self.path.relative_to(layer.root / "deployment-configuration")
        base = CHValues(
            layer.base.root / "deployment-configuration" / relative,
            layer.base,
        )
        return dict_merge(base.merge_with_base_and_envs(), own)

    def write(self, base, output_path=None):
        if output_path is None:
            target = self.path
        else:
            target = Path(output_path) / self.path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            yaml.dump(base, f)


class CHTemplate:
    def __init__(self, path: Path, parent: "CHProject | CHApp"):
        self.path = path
        self.project = parent


class CHInstance: ...


class CHContext:
    def __init__(self, path: Path, dockerfile: "CHDockerfile"):
        self.path = path
        self.dockerfile = dockerfile

    def redirect(self, new_root: Path, relative_to: Path) -> "CHContext":
        context = new_root.resolve().relative_to(relative_to.resolve(), walk_up=True)
        return CHContext(context, self.dockerfile)

    def resolve_for_build(self, relative_to: Path) -> "CHContext":
        entity = self.dockerfile.app
        if entity.base is None:
            return self
        destination = relative_to / MERGE_DIRNAME / entity.name
        shutil.rmtree(destination, ignore_errors=True)
        self.copy_my_context_to(destination)
        return self.redirect(destination, relative_to)

    def copy_my_context_to(self, destination: Path) -> None:
        _merge_base_chain(self.dockerfile.app, lambda e: e.build_context, destination)


class CHBaseImage:
    def __init__(self, path: Path, parent: "CHProject"):
        self.path = path
        self.app = parent
        self.name = self.path.name
        self._dockerfile = CHDockerfile(own_dockerfile_path(self.path), self)

    @property
    @lru_cache
    def base(self) -> "CHBaseImage | None":
        lower = self.containing_project.base
        return lower.base_images.get(self.name) if lower is not None else None

    @property
    def containing_project(self):
        return self.app

    @property
    def project(self):
        return self.app.project

    @property
    def dockerfile(self) -> "CHDockerfile":
        own = self._dockerfile.resolved
        if not own.exists() and self.base:
            return self.base.dockerfile
        return own

    @property
    def build_context(self) -> Path:
        if self.path.parent.name != "base-images":
            return self.path
        return self.containing_project.root

    @property
    def image_name(self):
        return f"{self.project.base_image_name()}/{self.name}"

    def build_dependencies(self) -> list["CHApp | CHBaseImage | CHAppTask | str"]:
        return []

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name!r} at {hex(id(self))}>"


class CHAppTask:
    def __init__(self, path: Path, parent: "CHApp | CHBaseImage"):
        self.path = path
        self.app = parent
        self._dockerfile = CHDockerfile(own_dockerfile_path(self.path), self)

    @property
    @lru_cache
    def base(self) -> "CHAppTask | None":
        lower = self.containing_project.base
        return lower.all_buildable_tasks().get(self.name) if lower is not None else None

    @property
    def name(self):
        return f"{self.app.name}-{self.path.name}"

    @property
    def containing_project(self) -> "CHProject":
        return self.app.containing_project

    @property
    def project(self) -> "CHProject":
        return self.app.project

    @property
    def dockerfile(self) -> "CHDockerfile":
        own = self._dockerfile.resolved
        if not own.exists() and self.base:
            return self.base.dockerfile
        return own

    @property
    def build_context(self) -> Path:
        return self.path

    @property
    def readme(self) -> Path:
        return self.path / "README.md"

    @property
    def image_name(self):
        return f"{self.app.image_name}-{self.path.name}"

    def build_dependencies(self) -> list["CHApp | CHBaseImage | CHAppTask | str"]:
        return []

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} at {hex(id(self))}>"


class CHDockerfile:
    def __init__(self, path: Path, parent: "CHApp | CHAppTask | CHBaseImage"):
        self.path = path
        self.app = parent

    def exists(self):
        return self.path.exists()

    @property
    def resolved(self) -> "CHDockerfile":
        for env in self.app.project.config.envs:
            env_path = self.path.with_name(f"{env}.Dockerfile")
            if env_path.exists():
                return CHDockerfile(env_path, self.app)
        return self

    def resolve_context(self, relative_to: Path) -> "CHContext":
        context = self.app.build_context.resolve().relative_to(
            relative_to.resolve(), walk_up=True
        )
        dockerfile_path = self.path.resolve().relative_to(
            self.app.build_context.resolve()
        )
        return CHContext(context, CHDockerfile(dockerfile_path, self.app))

    @property
    def base_images(self) -> dict[str, str]:
        """Gets the ARGS from a Dockerfile image (if ARGS is used directly in the FROM of the Dockerfile)"""
        if not self.exists():
            return {}
        content = self.path.read_text()
        found_args = {}
        args: dict[str, str] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            cmd, *rest = line.split()
            arg = rest[0] if len(rest) > 0 else ""
            match cmd:
                case "ARG" if "=" in rest[0]:
                    key, val = arg.split("=")
                    found_args[key] = val
                case "FROM" if arg[1:] in found_args:  # $NAME case
                    key = arg[1:]
                    args[key] = found_args[key]
                case "FROM" if arg[2:-1] in found_args:  # ${NAME} case
                    key = arg[2:-1]
                    args[key] = found_args[key]
                case _:
                    continue
        return args

    @property
    def base_dependencies(self) -> list["CHApp | CHBaseImage | CHAppTask | str"]:
        if not self.exists():
            return []

        project = self.app.project
        instructions = parse_dockerfile(self.path)
        arg_names = {
            instruction[1] for instruction in instructions if instruction[0] == "ARG"
        }

        dependencies = []
        for instruction in instructions:
            if instruction[0] != "FROM":
                continue
            ref = instruction[1]
            if ref not in arg_names:
                continue

            name = ref.lower().replace("_", "-")
            entity = (
                project.scanned_apps.get(name)
                or project.base_images.get(name)
                or project.all_buildable_tasks().get(name)
            )
            dependencies.append(entity.dockerfile if entity is not None else name)
        return dependencies


def _default_test_unit_enabled(harness: dict) -> dict:
    unit = resolve_path(harness, "test.unit")
    if isinstance(unit, dict) and "enabled" not in unit:
        return dict_merge(harness, {"test": {"unit": {"enabled": False}}})
    return harness


def _finalize_app_names(name: str, harness: dict) -> dict:
    harness = {**harness, "name": name}
    for key, default_name in (("service", name), ("deployment", name)):
        block = harness.get(key)
        if isinstance(block, dict) and not block.get("name"):
            harness = {**harness, key: {**block, "name": default_name}}

    database = harness.get("database")
    if isinstance(database, dict) and not database.get("name"):
        harness = {**harness, "database": {**database, "name": f"{name}-db"}}
    return harness


def _drop_mountpathless_volume(harness: dict) -> dict:
    deployment = harness.get("deployment")
    if not isinstance(deployment, dict):
        return harness
    volume = deployment.get("volume")
    if not isinstance(volume, dict) or volume.get("mountpath"):
        return harness
    if volume.get("name") or volume.get("size"):
        raise InvalidVolumeConfigurationError(
            f"Bad volume specified for application {harness.get('name')}: mountpath is required"
        )
    deployment = {k: v for k, v in deployment.items() if k != "volume"}
    return {**harness, "deployment": deployment}


def _promote_legacy_top_level_fields(value: dict, harness: dict) -> dict:
    value = {**value, "name": harness["name"]}
    deployment = harness.get("deployment") or {}
    if deployment.get("image"):
        value["image"] = deployment["image"]
    if deployment.get("port"):
        value["port"] = deployment["port"]
    if "resources" in deployment:
        value["resources"] = deployment["resources"]
    return value


def _finalize_app_values(
    name: str,
    value: dict,
    image: str | None = None,
    task_images: dict[str, str] | None = None,
) -> dict:
    harness = dict(value.get("harness") or {})
    harness = _default_test_unit_enabled(harness)
    harness = _finalize_app_names(name, harness)
    harness = _drop_mountpathless_volume(harness)
    deployment_image = resolve_path(harness, "deployment.image") or value.get("image")
    if image is not None:
        harness = {
            **harness,
            "deployment": {**(harness.get("deployment") or {}), "image": image},
        }
    value = {**value, "harness": harness, "build": not bool(deployment_image)}
    if task_images:
        value["task-images"] = task_images
    return _promote_legacy_top_level_fields(value, harness)


def register_file(key: str, path: Callable[[Path], Path], only_env: bool = False):

    def clsdescr(cls):
        CHProject._extregister.append((cls, key, path, only_env))
        return cls

    return clsdescr


class CHProject:
    _extregister: list[tuple[type, str, Callable[[Path], Path], bool]] = []

    def __init__(
        self,
        root: str | Path,
        base: "CHProject | None" = None,
        config: "CHDeployConfig | None" = None,
    ):
        self.root = Path(root)
        resolved_config = config if config else CHDeployConfig()
        self.base = base
        self._overlay: CHProject | None = None
        if base is not None:
            if base._overlay is not None:
                raise ValueError(
                    f"{base.root} is already layered under another project - "
                    "construct a fresh CHProject per layer for each build."
                )
            base._overlay = self
        self.config = resolved_config
        self.valuesyaml = CHValues(
            self.root / "deployment-configuration" / "values-template.yaml", self
        )
        self.customvalues_template = CHValues(
            self.root / "custom-values-template.yaml", self
        )
        self.app_defaults = CHValues(
            self.root / "deployment-configuration" / "value-template.yaml", self
        )
        self.helm_chart = CHValues(
            self.root / "deployment-configuration" / "helm" / "Chart.yaml", self
        )
        self.helm_values_defaults = CHValues(
            self.root / "deployment-configuration" / "helm" / "values.yaml", self
        )
        for cls, key, path, no_base in self._extregister:
            p = (
                CHValues.path_for_env(path(self.root), self.config.envs)
                if no_base and self.config.envs
                else path(self.root)
            )
            setattr(self, key, cls(p, self))

    @property
    @lru_cache
    def own_apps(self) -> dict[str, CHApp]:
        return {p.name: CHApp(p, self) for p in self.root.glob("applications/*/")}

    @property
    @lru_cache
    def scanned_apps(self) -> dict[str, "CHApp"]:
        merged = dict(self.base.scanned_apps) if self.base is not None else {}
        merged.update(self.own_apps)
        return merged

    @property
    @lru_cache
    def own_base_images(self) -> dict[str, CHBaseImage]:
        images: dict[str, CHBaseImage] = {}
        for relative_glob in (
            "infrastructure/base-images/*/",
            "infrastructure/common-images/*/",
        ):
            for p in self.root.glob(relative_glob):
                images[p.name] = CHBaseImage(p, self)
        return images

    @property
    @lru_cache
    def base_images(self) -> dict[str, CHBaseImage]:
        merged = dict(self.base.base_images) if self.base is not None else {}
        merged.update(self.own_base_images)
        return merged

    def __getitem__(self, key) -> "CHApp":
        try:
            return self.scanned_apps[key]
        except KeyError:
            msg = f"Coulnd't find app named {key} in {self.root}"
            if self.base is not None:
                msg = f"{msg} or in its base layers"
            raise AppUnknownError(msg)

    @property
    def containing_project(self) -> "CHProject":
        return self

    @property
    def project(self) -> "CHProject":
        top = self
        while top._overlay is not None:
            top = top._overlay
        return top

    @property
    @lru_cache
    def soft_dependencies(self):
        return self.all_dependencies()[0]

    @property
    @lru_cache
    def hard_dependencies(self):
        return self.all_dependencies()[1]

    @property
    @lru_cache
    def involved_apps(self):
        return set(
            itertools.chain(self.entrypoint_apps().values(), *self.all_dependencies())
        )

    @lru_cache
    def entrypoint_apps(self):
        includes = self.config.includes
        excludes = self.config.excludes
        is_included = lambda app: (
            (len(includes) > 0 and app in includes) or len(includes) == 0
        )
        is_not_excluded = lambda app: app not in excludes
        return {
            app_name: app
            for app_name, app in self.scanned_apps.items()
            if is_included(app_name) and is_not_excluded(app_name)
        }

    @lru_cache
    def all_dependencies(self):
        softs: set[CHApp | str] = set()
        hards: set[CHApp | str] = set()
        seen: set[str] = set()
        stack: list[CHApp | str] = list(self.entrypoint_apps().values())
        while stack:
            app = stack.pop()
            if isinstance(app, str) or app.name in seen:
                continue
            seen.add(app.name)
            new_soft = app.soft_dependencies
            new_hard = app.hard_dependencies
            softs.update(new_soft)
            hards.update(new_hard)
            stack.extend(new_soft)
            stack.extend(new_hard)
        return softs, hards

    @lru_cache
    def all_buildable_tasks(self):
        tasks = {}
        for app in self.scanned_apps.values():
            tasks.update(app._scan_tasks())
        return tasks

    @lru_cache
    def all_source_images(self) -> dict[str, str]:
        images: dict[str, str] = {}
        for app in self.involved_apps:
            if isinstance(app, str):
                continue
            images.update(app.dockerfile.base_images)
        for base_image in self.base_images.values():
            images.update(base_image.dockerfile.base_images)
        return images

    def _combined_dependencies(self, entity: CHApp | CHBaseImage | CHAppTask):
        explicit = entity.build_dependencies()
        for dep in explicit:
            if isinstance(dep, str):
                msg = f"Build dependency {dep!r} declared by {entity.name} is not a known app, base image, or task"
                raise DependencyUnknownError(msg)
        guessed = [
            dep if isinstance(dep, str) else dep.app
            for dep in entity.dockerfile.base_dependencies
        ]
        return [*explicit, *guessed]

    def _is_suppressed_orphan_task(self, dependency) -> bool:
        if self.config.manage_task_images or not isinstance(dependency, CHAppTask):
            return False
        involved_names = {
            app.name for app in self.involved_apps if not isinstance(app, str)
        }
        return dependency.app.name not in involved_names

    def all_build_dependencies(self, already_covered=()):
        needed = {}
        stack = []
        for app in self.involved_apps:
            if isinstance(app, str):
                continue
            stack.extend(self._combined_dependencies(app))

        while stack:
            dependency = stack.pop()
            if isinstance(dependency, str) or dependency.name in needed:
                continue
            if dependency.name in already_covered:
                continue
            if self._is_suppressed_orphan_task(dependency):
                continue
            needed[dependency.name] = dependency
            stack.extend(self._combined_dependencies(dependency))

        return needed

    def qualify(self, image_name):
        registry = self.config.registry
        if registry and not registry.endswith("/"):
            registry = f"{registry}/"
        return f"{registry}{image_name}"

    @property
    def _use_content_hash_tag(self) -> bool:
        return not self.config.tag and not self.config.local

    @property
    def _concrete_involved_apps(self) -> tuple[CHApp, ...]:
        return tuple(app for app in self.involved_apps if not isinstance(app, str))

    def _is_buildable_app(self, app: CHApp) -> bool:
        return app.dockerfile.exists() and not app.deployment_config.get("image")

    def _buildable_tasks(self, app: CHApp) -> list[CHAppTask]:
        return [t for t in app.tasks.values() if t.dockerfile.exists()]

    def _hashable_entities(self) -> dict[str, CHApp | CHBaseImage | CHAppTask]:
        entities: dict[str, CHApp | CHBaseImage | CHAppTask] = {}
        for app in self._concrete_involved_apps:
            if self._is_buildable_app(app):
                entities[app.name] = app
            entities.update({t.name: t for t in self._buildable_tasks(app)})
        entities.update(self.all_build_dependencies())
        return entities

    @lru_cache
    def _content_hash_tags(self) -> dict[str, str]:
        entities = self._hashable_entities()
        tags: dict[str, str] = {}
        own_hashes: dict[str, str] = {}
        visiting: set[str] = set()

        def own_hash(entity) -> str:
            if entity.name not in own_hashes:
                own_hashes[entity.name] = content_hash(
                    entity.dockerfile.app.build_context
                )
            return own_hashes[entity.name]

        def resolve(entity) -> str:
            if entity.name in tags:
                return tags[entity.name]
            if entity.name in visiting:
                return hashlib.sha1(own_hash(entity).encode("utf-8")).hexdigest()
            visiting.add(entity.name)
            deps = [
                d
                for d in self._combined_dependencies(entity)
                if not isinstance(d, str) and d.name in entities
            ]
            dep_tags = "".join(resolve(d) for d in deps)
            tags[entity.name] = hashlib.sha1(
                (own_hash(entity) + dep_tags).encode("utf-8")
            ).hexdigest()
            visiting.discard(entity.name)
            return tags[entity.name]

        for entity in entities.values():
            resolve(entity)
        return tags

    def qualify_image(self, entity: "CHApp | CHBaseImage | CHAppTask") -> str:
        qualified = self.qualify(entity.image_name)
        if self._use_content_hash_tag:
            tag = self._content_hash_tags().get(entity.name)
        else:
            tag = self.config.tag
        return f"{qualified}:{tag}" if tag else qualified

    @lru_cache
    def _app_task_images(self, app: "CHApp") -> dict[str, str]:
        return {
            task.name: self.qualify_image(task) for task in self._buildable_tasks(app)
        }

    @lru_cache
    def all_task_images(self) -> dict[str, str]:
        already_deployed = tuple(app.name for app in self._concrete_involved_apps)
        images = {
            name: self.qualify_image(dependency)
            for name, dependency in self.all_build_dependencies(
                already_deployed
            ).items()
        }
        for app in self._concrete_involved_apps:
            images.update(self._app_task_images(app))
        return images

    @lru_cache
    def all_values(self):
        app_values = {}
        for app in self.involved_apps:
            if isinstance(app, str):
                if app in self.soft_dependencies:
                    # A soft dependency is optional by definition
                    continue
                msg = f"Dependency {app} is declared as a hard dependency but cannot be found in the known applications: {list(self.scanned_apps.keys())}"
                raise DependencyUnknownError(msg)
            app_values[app.name] = app.all_values()
        values = dict_merge(
            dict_merge(
                self.helm_values_defaults.merge_with_base_and_envs(), app_values
            ),
            self.valuesyaml.merge_with_base_and_envs(),
        )
        if "name" not in values:
            chart_name = self.helm_chart.merge_with_base_and_envs().get("name")
            if chart_name:
                values = {**values, "name": chart_name.lower()}
        return values

    def base_image_name(self):
        return self.all_values()["name"]

    def _buildable_image(self, app: "CHApp") -> str | None:
        return self.qualify_image(app) if self._is_buildable_app(app) else None

    def build_final_helm_values(self, write_on_disk=True) -> HarnessMainConfig:
        involved_apps = {app.name: app for app in self._concrete_involved_apps}
        values = self.all_values()
        apps = {
            name: _finalize_app_values(
                name,
                value,
                self._buildable_image(involved_apps[name]),
                self._app_task_images(involved_apps[name]),
            )
            for name, value in values.items()
            if name in involved_apps
        }
        project_values = {
            key: value for key, value in values.items() if key not in involved_apps
        }

        ingress = dict(project_values.get("ingress") or {})
        if ingress:
            ingress["ssl_redirect"] = (
                bool(ingress.get("ssl_redirect")) and self.config.tls
            )
            project_values = {**project_values, "ingress": ingress}

        source_images = {
            **self.all_source_images(),
            **(project_values.get("source_images") or {}),
        }

        final_allvalues = {
            **project_values,
            "apps": apps,
            "task-images": self.all_task_images(),
            "source_images": source_images,
            "local": self.config.local,
            "secured_gatekeepers": self.config.secured_gatekeepers,
            "tls": self.config.tls,
        }
        if self.config.domain:
            final_allvalues["domain"] = self.config.domain
        if self.config.namespace:
            final_allvalues["namespace"] = self.config.namespace
        if self.config.tag:
            final_allvalues["tag"] = self.config.tag
        if self.config.registry:
            registry = {"name": self.config.registry}
            if self.config.registry_secret_name:
                registry["secret"] = {"name": self.config.registry_secret_name}
            final_allvalues["registry"] = registry

        helm_values = HarnessMainConfig.from_dict(final_allvalues)
        helm_values._ch_project = self

        if write_on_disk:
            CHValues(
                Path(self.config.output_path) / "helm" / "values.yaml", self
            ).write(helm_values.to_dict())

        return helm_values

    def write_chart(self) -> None:
        dest = Path(self.config.output_path) / "helm"
        shutil.rmtree(dest, ignore_errors=True)
        _merge_base_chain(
            self, lambda p: p.root / "deployment-configuration" / "helm", dest
        )
        for app in self.involved_apps:
            if isinstance(app, str):
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
        collect_and_merge_env_specific_files(dest, self.config.envs)


@dataclass
class CHDeployConfig:
    env: str | list[str] | None = field(default=None, kw_only=True)
    includes: list[str] = field(default_factory=list, kw_only=True)
    excludes: list[str] = field(default_factory=list, kw_only=True)
    registry: str = field(default="", kw_only=True)
    tag: str | None = field(default=None, kw_only=True)
    local: bool = field(default=False, kw_only=True)
    namespace: str | None = field(default=None, kw_only=True)
    backend: Literal["helm", "compose"] = field(default="helm", kw_only=True)
    registry_secret_name: str | None = field(default=None, kw_only=True)
    domain: str = field(default="cloudharness.metacell.us", kw_only=True)
    debug: bool = field(default=False, kw_only=True)
    tls: bool = field(default=True, kw_only=True)
    output_path: str = field(default="./deployment", kw_only=True)
    manage_task_images: bool = field(default=True, kw_only=True)
    secured_gatekeepers: bool = field(default=True, kw_only=True)

    @property
    def envs(self) -> list[str]:
        if not self.env:
            return []
        return [self.env] if isinstance(self.env, str) else list(self.env)
