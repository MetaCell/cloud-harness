import dataclasses
import itertools
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

from ruamel.yaml import YAML

yaml = YAML(typ="safe")


KEY_TASK_IMAGES = "task-images"


from .utils import dict_merge, merge_with_layer


def resolve_path(d, p, default=None):
    obj = d
    for frag in p.split("."):
        if obj is None:
            return default
        obj = obj.get(frag)
    return obj if obj is not None else default


class TaskUnknownError(Exception): ...


class AppUnknownError(Exception): ...


class DependencyUnknownError(Exception): ...


class CHApp:
    def __init__(self, path: Path, parent: "CHProject | CHApp"):
        self.path = path
        self.parent = parent
        self.name = self.path.name
        tasks: dict[str, CHAppTask] = {}
        for t in self.path.glob("tasks/*/"):
            task = CHAppTask(t, self)
            tasks[task.name] = task
        self.tasks = tasks
        self.dockerfile = CHDockerfile(self.path / "Dockerfile", self)
        self.valuesyaml = CHValues(self.path / "deploy" / "values.yaml", self)

    def __getitem__(self, key) -> "CHAppTask":
        try:
            return self.tasks[key]
        except KeyError:
            raise TaskUnknownError(f"App {self.name} doesn't own a {key} task")

    @property
    @lru_cache
    def project(self) -> "CHProject":
        project = self.parent
        while isinstance(project, CHApp):
            project = project.parent
        return project

    @lru_cache
    def all_values(self):
        base = self.valuesyaml
        layer = base.for_env(self.project.config.env)
        return base.merge_with(layer)

    @property
    @lru_cache
    def templates(self) -> list["CHTemplate"]:
        path = self.path / "deploy" / "templates"
        return [
            CHTemplate(p, self)
            for p in itertools.chain(path.rglob("*.yaml"), path.rglob("*.tpl"))
        ]

    def add_task(self, name):
        self.tasks[name] = CHAppTask(self.path / name, self)

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

    def build_dependencies(self) -> list["CHApp | str"]:
        return [
            self.project.scanned_apps.get(dep, dep)
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
    def image_name(self):
        return f"{self.project.base_image_name()}/{
            resolve_path(
                self.harness_config, 'image_name', default=self.dockerfile.app.name
            )
        }"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name!r} at {hex(id(self))}>"


class CHValues:
    def __init__(self, path: Path, parent: "CHApp | CHProject", env: str | None = None):
        self.app: CHApp | CHProject = parent
        self.path: Path = path
        self.env: str | None = env

    @property
    def project(self):
        return self.app.project

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
        return path.with_name(f"{path.stem}-{env}{path.suffix}")

    def for_env(self, env: str | None):
        if env is None:
            return self

        return CHValues(self.path_for_env(self.path, env), self.app, env)

    def merge_with(self, other):
        return merge_with_layer(self, other)

    def write(self, base):
        with self.path.open("w", encoding="utf-8") as f:
            yaml.dump(base, f)


class CHTemplate:
    def __init__(self, path: Path, parent: "CHProject | CHApp"):
        self.path = path
        self.project = parent


class CHInstance: ...


class CHAppTask:
    def __init__(self, path: Path, parent: CHApp):
        self.path = path
        self.app = parent
        self.dockerfile = CHDockerfile(self.path / "Dockerfile", self)

    @property
    def name(self):
        return f"{self.app.name}-{self.path.name}"

    @property
    def readme(self) -> Path:
        return self.path / "README.md"

    @property
    def image_name(self):
        return f"{self.app.image_name}-{self.path.name}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} at {hex(id(self))}>"


class CHDockerfile:
    def __init__(self, path: Path, parent: CHApp | CHAppTask):
        self.path = path
        self.app = parent

    @property
    def base_images(self) -> dict[str, str]:
        """Gets the ARGS from a Dockerfile image (if ARGS is used directly in the FROM of the Dockerfile)"""
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
        cloudharness_path: str | Path | None = None,
        config: "CHDeployConfig | None" = None,
    ):
        self.root = Path(root)
        self.ch_path = Path(cloudharness_path) if cloudharness_path else self.root
        self.scanned_apps: dict[str, CHApp] = {
            p.name: CHApp(p, self)
            for p in itertools.chain(
                self.ch_path.glob("applications/*/"), self.root.glob("applications/*/")
            )
        }
        self.valuesyaml = CHValues(
            self.root / "deployment-configuration" / "values-template.yaml", self
        )
        self.customvalues_template = CHValues(
            self.root / "custom-values-template.yaml", self
        )
        self.config = config if config else CHDeployConfig()
        self.soft_dependencies, self.hard_dependencies = self.all_dependencies()
        self.involved_apps = set(
            itertools.chain(self.entrypoint_apps().values(), *self.all_dependencies())
        )
        self.helm_chart = CHValues(
            self.root / "deployment-configuration" / "helm" / "Chart.yaml", self
        )
        for cls, key, path, no_base in self._extregister:
            p = (
                CHValues.path_for_env(path(self.root), self.config.env)
                if no_base
                else path(self.root)
            )
            setattr(self, key, cls(p, self))

    def __getitem__(self, key) -> "CHApp":
        try:
            return self.scanned_apps[key]
        except KeyError:
            msg = f"Coulnd't find app named {key} in {self.root} or in {self.ch_path}"
            if self.ch_path != self.root:
                msg = f"{msg} or in {self.ch_path}"
            raise AppUnknownError(msg)

    @property
    def project(self) -> "CHProject":
        return self

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
    def all_tasks(self):
        tasks = {}
        for app in self.involved_apps:
            if isinstance(app, str):
                continue
            tasks.update(app.tasks)
        return tasks

    @lru_cache
    def all_values(self):
        app_values = {}
        for app in self.involved_apps:
            if isinstance(app, str):
                msg = f"Dependency {app} is declared as dependency but cannot be found in the known applications: {list(self.scanned_apps.keys())}"
                if not self.config.skip_unknown_deps:
                    raise DependencyUnknownError(msg)
                print(msg)
                continue
            app_values[app.name] = app.all_values()
        base = self.valuesyaml
        return dict_merge(
            dict_merge(base.merge_with(base.for_env(self.config.env)), app_values),
            self.helm_chart.all_raw_values(),
        )

    def base_image_name(self):
        return self.all_values()["name"]


@dataclass
class CHDeployConfig:
    env: str | None = field(default=None, kw_only=True)
    includes: list[str] = field(default_factory=list, kw_only=True)
    excludes: list[str] = field(default_factory=list, kw_only=True)
    skip_unknown_deps: bool = field(default=False, kw_only=True)
    registry: str = field(default="", kw_only=True)
    tag: str | None = field(default=None, kw_only=True)
    local: bool = field(default=False, kw_only=True)
    namespace: str | None = field(default=None, kw_only=True)
    backend: Literal["helm", "compose"] = field(default="helm", kw_only=True)
