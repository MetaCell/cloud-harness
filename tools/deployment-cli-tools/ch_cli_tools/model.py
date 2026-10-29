"""ch_cli_tools.model - the CloudHarness deployment model.

A deployment is built from one or more root directories (cloud-harness itself, a
platform layer, a project layer, ...), each scanned into its own CHProject and
layered over the previous one via `.base` (`.project` is the top of that chain).
Every entity that can be overridden - CHApp, CHBaseImage, CHAppTask, CHValues -
mirrors this layering through its own `.base`, so a higher layer can override or
merge whatever a lower layer already declared, without reconstructing it.

CHApp is an application CHProject found on disk - not necessarily one that ends up
deployed (CHApp.is_involved answers that, from the project's include/exclude config
and dependency graph). CHAppInstance is a named instance of an app
(deploy/instances/<name>/), deployed as its own app, inheriting the parent's build.

CHBaseImage/CHTestImage are shared images built outside of any application
(infrastructure/base-images, infrastructure/common-images, test/); CHAppTask is a
buildable task owned by an app or base image. All three resolve their own
CHDockerfile and can produce a CHContext - their build context, merged across base
layers - to actually build it.

CHValues wraps one values.yaml-shaped file, resolved across environments
(values-<env>.yaml) and, for project-level files, across base layers too.
CHDeployConfig carries the deploy-time knobs (includes/excludes/env/tag/...) shared
by the whole chain.

```mermaid
classDiagram
    class CHDeployConfig
    class CHProject {
        +base: CHProject
        +config: CHDeployConfig
        +scanned_apps: Dict~CHApp~
        +base_images: Dict~CHBaseImage~
        +involved_apps
    }
    class CHApp {
        +base: CHApp
        +is_buildable
        +is_involved
        +buildable_image
    }
    class CHAppInstance {
        +parent_app: CHApp
    }
    class CHBaseImage {
        +base: CHBaseImage
    }
    class CHTestImage
    class CHAppTask {
        +base: CHAppTask
    }
    class CHDockerfile
    class CHContext
    class CHValues
    class CHOpenAPI
    class CHTemplate

    CHProject --> CHDeployConfig : config
    CHProject "0..1" --> "0..1" CHProject : base
    CHProject "1" o-- "*" CHApp : scanned_apps
    CHProject "1" o-- "*" CHBaseImage : base_images
    CHBaseImage <|-- CHTestImage
    CHApp <|-- CHAppInstance
    CHApp "1" o-- "*" CHAppTask : tasks
    CHApp "1" o-- "*" CHAppInstance : instances
    CHApp "0..1" --> "0..1" CHApp : base
    CHApp --> CHDockerfile : dockerfile
    CHApp --> CHValues : app_basevalues_template
    CHApp --> CHOpenAPI : openapi
    CHApp --> CHTemplate : templates
    CHBaseImage --> CHDockerfile : dockerfile
    CHBaseImage "0..1" --> "0..1" CHBaseImage : base
    CHAppTask --> CHDockerfile : dockerfile
    CHAppTask "0..1" --> "0..1" CHAppTask : base
    CHDockerfile --> CHContext : resolve_context()
```
"""

import copy
import hashlib
import itertools
import logging
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

from cloudharness_model import HarnessMainConfig  # type: ignore

from ch_cli_tools.configuration.secrets import secret_definition_error  # type: ignore

from .utils import (
    MERGE_DIRNAME,
    _merge_base_chain,
    content_hash,
    dict_merge,  # type: ignore
    env_suffixed_path,
    find_files,
    get_yaml_parser,
    merge_with_layer,
    own_dockerfile_path,
    parse_dockerfile,
    resolve_path,
)

KEY_HARNESS = "harness"
KEY_SERVICE = "service"
KEY_DATABASE = "database"
KEY_DEPLOYMENT = "deployment"
KEY_APPS = "apps"
KEY_TASK_IMAGES = "task-images"
KEY_TEST_IMAGES = "test-images"
_ENTRYPOINT_OVERRIDE_PATTERN = re.compile(
    r"CLOUDHARNESS_FLASK|gunicorn|CLOUDHARNESS_DJANGO", re.IGNORECASE
)


class TaskUnknownError(KeyError):
    """Raised when an app has no such task."""


class AppUnknownError(KeyError):
    """Raised when no app matches a lookup."""


class DependencyUnknownError(Exception):
    """Raised when a declared dependency can't be resolved."""


class InvalidVolumeConfigurationError(Exception):
    """Raised for a malformed volume configuration."""


class ValuesValidationError(Exception):
    """Raised when harness values fail validation."""


class CHUnitTest:
    """harness.test.unit configuration."""

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
    """harness.test.api configuration."""

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
    """harness.test.e2e configuration."""

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
    """harness.test configuration (unit/api/e2e)."""

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


def _base_chain(entity):
    """`entity` followed by every entity reachable by repeatedly following
    `.base` - shared by CHProject.all_layers and CHApp.all_layers, since both
    are the same walk over a different `.base`-linked type."""
    chain = []
    while entity is not None:
        chain.append(entity)
        entity = entity.base
    return chain


class CHApp:
    """An application belonging to a CHProject, not necessarily part of the final deployment - see is_involved."""

    def __init__(self, path: Path, parent: "CHProject"):
        """Resolves the app's Dockerfile and base layer, then scans its own tasks and instances."""
        self.path = path
        self.parent = parent
        self.name = self.path.name
        self._dockerfile = CHDockerfile(own_dockerfile_path(self.path), self)
        self.app_basevalues_template = CHValues(
            self.path / "deploy" / "values.yaml", self
        )
        self.openapi = CHOpenAPI(self.path / "api" / "openapi.yaml", self)
        self.base: CHApp | None = (
            parent.base.scanned_apps.get(self.name) if parent.base is not None else None
        )
        tasks: dict[str, CHAppTask] = {}
        if self.base is not None:
            for name, task in self.base._tasks.items():
                tasks[name] = CHAppTask(task.path, self)
        for t in self.path.glob("tasks/*/"):
            task = CHAppTask(t, self)
            tasks[task.name] = task
        self._tasks = tasks
        self.instances: dict[str, CHAppInstance] = {
            name: CHAppInstance(self, name) for name in self.instance_names
        }

    def exists(self):
        return self.path.exists()

    @property
    def dockerfile(self) -> "CHDockerfile":
        """This app's Dockerfile, own or inherited from its base layer."""
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
        """This app's own values merged over its base layer's."""
        own = self.app_basevalues_template.merge_with_envs(self.project.config.envs)
        if self.base is None:
            return own
        return dict_merge(self.base.raw_values(), own)

    @lru_cache
    def all_values(self):
        """Project-wide app defaults merged under this app's raw values."""
        return dict_merge(
            self.project.app_defaults.merge_with_base_and_envs(),
            self.raw_values(),
        )

    @property
    def tasks(self) -> dict[str, "CHAppTask"]:
        return {
            name: task
            for name, task in self._tasks.items()
            if name not in self.project.config.excludes
        }

    @property
    def own_instance_names(self) -> set[str]:
        """This app's own instance directories that declare values for the active environment."""
        instances_dir = self.path / "deploy" / "instances"
        envs = self.project.config.envs
        names = set()
        for p in instances_dir.glob("*/"):
            if p.name.startswith("."):
                continue
            candidates = (
                p / "values.yaml",
                *(p / f"values-{env}.yaml" for env in envs),
            )
            if any(c.exists() for c in candidates):
                names.add(p.name)
        return names

    @property
    def instance_names(self) -> set[str]:
        names = set(self.own_instance_names)
        if self.base is not None:
            names |= self.base.instance_names
        return names

    @property
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
        return resolve_path(self.all_values(), "harness") or {}

    @property
    def soft_dependencies(self) -> list["CHApp | str"]:
        """Soft dependency names resolved to known apps, excluded ones dropped."""
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
        """Hard dependency, resolved to known apps; raises an exception if one is excluded."""
        deps = []
        for dep in cast(
            list[str],
            resolve_path(self.harness_config, "dependencies.hard", default=[]),
        ):
            if dep in self.project.config.excludes:
                raise DependencyUnknownError(
                    f"Hard dependency {dep!r} declared by {self.name} is excluded from this deployment"
                )
            deps.append(self.project.scanned_apps.get(dep, dep))
        return deps

    def build_dependencies(self) -> list["CHApp | CHBaseImage | CHAppTask | str"]:
        """Build dependencies, resolved against apps, base images and tasks."""
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
    def secrets(self) -> dict:
        return resolve_path(self.harness_config, "secrets", default={}) or {}

    @property
    def database(self) -> dict:
        return resolve_path(self.harness_config, "database", default={}) or {}

    @property
    def app_entrypoint(self) -> Path | None:
        """Where the app's __main__.py lives, if its Dockerfile/requirements call for overriding the entrypoint."""
        candidates = sorted(
            find_files(self.build_context, "__main__.py"), key=lambda p: len(p.parts)
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

    @property
    def is_buildable(self) -> bool:
        """Whether CloudHarness should build this app's image."""
        if self.deployment_config.get("image_ref"):
            return False
        if self.dockerfile.exists():
            return not self.deployment_config.get("image")
        if self.deployment_config.get("image"):
            return False
        if self.deployment_config.get("auto"):
            raise ValuesValidationError(
                f"At least one Dockerfile must be specified for application {self.name}. "
                "Specify harness.deployment.image if you intend to use a prebuilt image."
            )
        return False

    @property
    def buildable_image(self) -> str | None:
        """The image this app will be built as, if it builds one."""
        image_ref = self.deployment_config.get("image_ref")
        if image_ref:
            dependency_images = {
                dep.name: self.project.qualify_image(dep)
                for dep in self.build_dependencies()
                if not isinstance(dep, str)
            }
            image = self.task_images.get(image_ref) or dependency_images.get(image_ref)
            if not image:
                raise ValuesValidationError(
                    f"harness.deployment.image_ref of application {self.name} is "
                    f"{image_ref!r}, which is not an image built for it: add it to "
                    "harness.dependencies.build, or name one of the application's task images"
                )
            return image
        return self.project.qualify_image(self) if self.is_buildable else None

    @property
    def buildable_tasks(self) -> list["CHAppTask"]:
        return [t for t in self.tasks.values() if t.dockerfile.exists()]

    @property
    def task_images(self) -> dict[str, str]:
        return {
            task.name: self.project.qualify_image(task) for task in self.buildable_tasks
        }

    @property
    def is_involved(self) -> bool:
        """Whether this app is actually part of the final deployment."""
        return self.name in {
            app.name for app in self.project.involved_apps if not isinstance(app, str)
        }

    def all_layers(self) -> list["CHApp"]:
        """This app and every layer it overrides, nearest first, this app included."""
        return _base_chain(self)

    def all_sub_layers(self) -> list["CHApp"]:
        """Every layer this app overrides, nearest first, this app not included."""
        return _base_chain(self.base)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name!r} at {hex(id(self))}>"


def instance_app_key(app_name: str, instance_name: str) -> str:
    return f"{app_name}-{instance_name}"


class CHAppInstance(CHApp):
    """A named instance of an application, deployed as its own app."""

    _HOST_KEYS = ("subdomain", "aliases", "domain")
    _NAMED_RESOURCES = ("service", "deployment", "database")

    def __init__(self, parent_app: CHApp, instance_name: str):
        """Mirrors CHApp's layout for an instance directory instead of an app one."""
        self.parent_app = parent_app
        self.instance_name = instance_name
        self.name = instance_app_key(parent_app.name, instance_name)
        self.path = parent_app.path / "deploy" / "instances" / instance_name
        self.parent = parent_app.containing_project
        self.base = (
            parent_app.base.instances.get(instance_name)
            if parent_app.base is not None
            else None
        )
        self._dockerfile = CHDockerfile(self.path / ".instance-never-builds", self)
        self.app_basevalues_template = CHValues(self.path / "values.yaml", self)
        self.openapi = parent_app.openapi
        self._tasks = {}

    @lru_cache
    def all_values(self) -> dict:
        return self._build_values(self.parent_app.all_values(), self.raw_values())

    @property
    def is_buildable(self) -> bool:
        return False

    @property
    def buildable_image(self) -> str | None:
        """The image this instance runs: its own, or the one its parent app builds."""
        own = self.deployment_config.get("image") or self.all_values().get("image")
        if own:
            return own
        return self.parent_app.buildable_image or self.parent_app.deployment_config.get(
            "image"
        )

    @staticmethod
    def _instance_sets(values: dict, *path: str) -> bool:
        """Whether the instance's own values explicitly set this path."""
        node = values
        for key in path[:-1]:
            if not isinstance(node, dict):
                return False
            node = node.get(key)
        return isinstance(node, dict) and path[-1] in node

    def _build_values(self, app_values: dict, instance_values: dict) -> dict:
        """The instance's values: the parent's, without its identity (host, names), with the instance's own overrides on top."""
        instance_app = copy.deepcopy(app_values)
        harness = instance_app.setdefault("harness", {})

        for key in self._HOST_KEYS:
            harness.pop(key, None)
        harness.pop("name", None)
        for key in self._NAMED_RESOURCES:
            resource = harness.get(key)
            if isinstance(resource, dict):
                resource.pop("name", None)

        instance_app = dict_merge(instance_app, instance_values)
        harness = instance_app["harness"]

        if "subdomain" not in (instance_values.get("harness") or {}):
            harness["subdomain"] = self.instance_name

        volume = (harness.get("deployment") or {}).get("volume") or {}
        if (
            volume.get("name")
            and volume.get("auto", True)
            and not self._instance_sets(
                instance_values, "harness", "deployment", "volume", "name"
            )
        ):
            volume["name"] = f"{self.instance_name}-{volume['name']}"

        database = harness.get("database") or {}
        if database.get("connect_string") and not self._instance_sets(
            instance_values, "harness", "database", "connect_string"
        ):
            database["connect_string"] = ""

        parent_database = (app_values.get("harness") or {}).get("database") or {}
        if database.get("name") and database["name"] == (
            parent_database.get("name") or f"{self.parent_app.name}-db"
        ):
            for database_type, type_config in database.items():
                if (
                    isinstance(type_config, dict)
                    and type_config.get("initialdb")
                    and not self._instance_sets(
                        instance_values,
                        "harness",
                        "database",
                        database_type,
                        "initialdb",
                    )
                ):
                    type_config["initialdb"] = self.name.replace("-", "_")

        instance_app["build"] = False
        instance_app[KEY_TASK_IMAGES] = {}

        return instance_app


class CHValues:
    """A values.yaml file, resolved across environments and base layers."""

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
            return yaml.load(f) or {}

    def exists(self):
        return self.path.exists()

    @classmethod
    def path_for_env(cls, path, env):
        """The env-suffixed sibling of path (values.yaml -> values-dev.yaml)."""
        suffix = env if isinstance(env, str) else "-".join(env)
        return env_suffixed_path(path, suffix)

    def for_env(self, env: str | None):
        if env is None:
            return self

        return CHValues(self.path_for_env(self.path, env), self.app, env)

    def merge_with(self, other):
        return merge_with_layer(self, other)

    def merge_with_envs(self, envs: list[str]) -> dict:
        """Base values merged with each environment-specific layer, in order."""
        result = self.all_raw_values() if self.exists() else {}
        for env in envs:
            layer = self.for_env(env)
            if layer.exists():
                result = dict_merge(result, layer.all_raw_values())
        return result

    def merge_with_base_and_envs(self) -> dict:
        """This file, merged with its counterpart in every base layer."""
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
        target = (
            self.path if output_path is None else Path(output_path) / self.path.name
        )
        self.write_on_disk(target, base)

    @classmethod
    def write_on_disk(cls, path: Path, data: dict) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)


class CHTemplate:
    """A Helm template file owned by an app."""

    def __init__(self, path: Path, parent: "CHProject | CHApp"):
        self.path = path
        self.project = parent


class CHContext:
    """A Docker build context, relocatable across merged base layers."""

    def __init__(self, path: Path, dockerfile: "CHDockerfile"):
        self.path = path
        self.dockerfile = dockerfile

    def redirect(self, new_root: Path, relative_to: Path) -> "CHContext":
        context = new_root.resolve().relative_to(relative_to.resolve(), walk_up=True)
        return CHContext(context, self.dockerfile)

    def resolve_for_build(self, relative_to: Path) -> "CHContext":
        """This entity's build context, merged across its base layers."""
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
    """A base/common image under infrastructure/."""

    def __init__(self, path: Path, parent: "CHProject"):
        self.path = path
        self.app = parent
        self.name = self.path.name
        self._dockerfile = CHDockerfile(own_dockerfile_path(self.path), self)

    def _lower_registry(self, lower: "CHProject") -> dict:
        return lower.base_images

    @property
    def base(self) -> "CHBaseImage | None":
        """This base image's counterpart one layer down, if any."""
        lower = self.containing_project.base
        if lower is None:
            return None
        return self._lower_registry(lower).get(self.name)

    @property
    def containing_project(self):
        return self.app

    @property
    def project(self):
        return self.app.project

    @property
    def dockerfile(self) -> "CHDockerfile":
        """This image's Dockerfile, own or inherited from its base layer."""
        own = self._dockerfile.resolved
        if not own.exists() and self.base:
            return self.base.dockerfile
        return own

    @property
    def build_context(self) -> Path:
        """Shared base images build from the project root; the rest build from their own directory."""
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


class CHTestImage(CHBaseImage):
    """A base image under test/."""

    def _lower_registry(self, lower: "CHProject") -> dict:
        return lower.test_images


class CHAppTask:
    """A buildable task owned by an app or base image."""

    def __init__(self, path: Path, parent: "CHApp | CHBaseImage"):
        self.path = path
        self.app = parent
        self._dockerfile = CHDockerfile(own_dockerfile_path(self.path), self)

    @property
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
        """This task's Dockerfile, own or inherited from its base layer."""
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


class CHOpenAPI:
    """An app's openapi.yaml spec."""

    def __init__(self, path: Path, parent: "CHApp"):
        self.path = path
        self.app = parent

    def exists(self) -> bool:
        return self.path.exists()

    @property
    @lru_cache
    def content(self) -> dict:
        if not self.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as f:
            return yaml.load(f)

    @property
    def server_urls(self) -> list[str]:
        return [server["url"] for server in (self.content.get("servers") or [])]


class CHDockerfile:
    """A Dockerfile, resolved across env and base overrides."""

    def __init__(self, path: Path, parent: CHApp | CHAppTask | CHBaseImage):
        self.path = path
        self.app = parent

    def exists(self):
        return self.path.exists()

    @property
    def resolved(self) -> "CHDockerfile":
        """The env-specific Dockerfile sibling, if one exists for the active environment."""
        for env in self.app.project.config.envs:
            env_path = self.path.with_name(f"{env}.Dockerfile")
            if env_path.exists():
                return CHDockerfile(env_path, self.app)
        return self

    def resolve_context(self, relative_to: Path) -> CHContext:
        """The build context and Dockerfile path, both relative to the given root."""
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
                case "ARG" if "=" in arg:
                    key, val = arg.split("=", maxsplit=1)
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
        """Apps, base images or tasks referenced via ARG in a FROM line."""
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
    """Defaults harness.test.unit.enabled to False when the block exists but doesn't say."""
    unit = resolve_path(harness, "test.unit")
    if isinstance(unit, dict) and "enabled" not in unit:
        return dict_merge(harness, {"test": {"unit": {"enabled": False}}})
    return harness


def _finalize_app_names(name: str, harness: dict) -> dict:
    """Defaults the service/deployment/database resource names to the app's name."""
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
    """Drops an auto volume lacking a mountpath; rejects one that was otherwise configured."""
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


def _clear_unused_db_configuration(harness: dict) -> dict:
    """Drops every database type's config except the one actually selected."""
    database = harness.get("database")
    if not isinstance(database, dict):
        return harness
    if database.get("type") is None:
        return {k: v for k, v in harness.items() if k != "database"}
    db_specific_keys = {
        k
        for k, v in database.items()
        if isinstance(v, dict) and "image" in v and "ports" in v
    }
    database = {
        k: v
        for k, v in database.items()
        if k not in db_specific_keys or k == database["type"]
    }
    return {**harness, "database": database}


def _promote_legacy_top_level_fields(value: dict, harness: dict) -> dict:
    """Copies a few deployment fields to the top level for legacy compatibility."""
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
    """Applies every per-app values finalization step and resolves its build flag."""
    harness = dict(value.get("harness") or {})
    harness = _default_test_unit_enabled(harness)
    harness = _finalize_app_names(name, harness)
    harness = _drop_mountpathless_volume(harness)
    harness = _clear_unused_db_configuration(harness)
    deployment_image = resolve_path(harness, "deployment.image") or value.get("image")
    image_ref = resolve_path(harness, "deployment.image_ref")
    if image is not None:
        harness = {
            **harness,
            "deployment": {**(harness.get("deployment") or {}), "image": image},
        }
    build = (
        False
        if (value.get("build") is False or image_ref)
        else not bool(deployment_image)
    )
    value = {**value, "harness": harness, "build": build}
    if task_images:
        value["task-images"] = task_images
    return _promote_legacy_top_level_fields(value, harness)


def register_file(key: str, path: Callable[[Path], Path], only_env: bool = False):
    """Registers an extra values file CHProject.__init__ should load for every layer."""

    def clsdescr(cls):
        CHProject._extregister.append((cls, key, path, only_env))
        return cls

    return clsdescr


class CHProject:
    """A deployment root, optionally layered over a base CHProject."""

    _extregister: list[tuple[type, str, Callable[[Path], Path], bool]] = []

    def __init__(
        self,
        root: str | Path,
        base: "CHProject | None" = None,
        config: "CHDeployConfig | None" = None,
    ):
        """Scans this project's own apps, base images and test images, merging them over its base layer's."""
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

        own_apps: dict[str, CHApp] = {
            p.name: CHApp(p, self) for p in self.root.glob("applications/*/")
        }
        self.own_apps = own_apps
        self.scanned_apps = dict(base.scanned_apps) if base is not None else {}
        self.scanned_apps.update(own_apps)

        own_base_images: dict[str, CHBaseImage] = {}
        for relative_glob in (
            "infrastructure/base-images/*/",
            "infrastructure/common-images/*/",
        ):
            for p in self.root.glob(relative_glob):
                own_base_images[p.name] = CHBaseImage(p, self)
        self.own_base_images = own_base_images
        self.base_images = dict(base.base_images) if base is not None else {}
        self.base_images.update(own_base_images)

        own_test_images: dict[str, CHTestImage] = {}
        for p in self.root.glob("test/*/"):
            image = CHTestImage(p, self)
            if image.dockerfile.exists():
                own_test_images[p.name] = image
        self.own_test_images = own_test_images

        self.test_images = dict(base.test_images) if base is not None else {}
        self.test_images.update(self.own_test_images)

    @classmethod
    def init(cls, root_paths, config: "CHDeployConfig | None" = None) -> "CHProject":
        """Builds the layer chain bottom-up from root_paths, lowest priority first."""
        project = None
        for path in root_paths:
            project = cls(path, base=project, config=config)
        assert project is not None, "root_paths must be non-empty"
        return project

    def all_layers(self) -> list["CHProject"]:
        """This project and every layer it overrides, nearest first, this project included."""
        return _base_chain(self)

    def all_sub_layers(self) -> list["CHProject"]:
        """Every layer this project overrides, nearest first, this project not included."""
        return _base_chain(self.base)

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
        """The top of the layer chain."""
        top = self
        while top._overlay is not None:
            top = top._overlay
        return top

    @property
    def soft_dependencies(self):
        return self.all_dependencies()[0]

    @property
    def hard_dependencies(self):
        return self.all_dependencies()[1]

    @property
    def involved_apps(self):
        """Every entrypoint, its dependencies, and their instances."""
        base = set(
            itertools.chain(self.entrypoint_apps().values(), *self.all_dependencies())
        )
        involved_names = {app.name for app in base if not isinstance(app, str)}
        instances = {
            instance
            for instance in self.all_instances().values()
            if instance.parent_app.name in involved_names
            and instance.name not in self.config.excludes
        }
        return base | instances

    @lru_cache
    def all_instances(self) -> dict[str, CHAppInstance]:
        """Every app's instances, keyed by their deployment key; raises on a name collision with a real app."""
        instances = {
            instance.name: instance
            for app in self.scanned_apps.values()
            if app.name not in self.config.excludes
            for instance in app.instances.values()
        }
        collisions = sorted(set(instances) & set(self.scanned_apps))
        if collisions:
            raise ValuesValidationError(
                f"Instance(s) {', '.join(collisions)} collide with an existing application "
                "name - rename the instance or the application"
            )
        return instances

    def entrypoint_apps(self):
        """Apps and instances selected by --include/--exclude; instances always follow their parent."""
        includes = self._includes_with_instances()
        excludes = self.config.excludes

        def is_included(app):
            return (len(includes) > 0 and app in includes) or len(includes) == 0

        def is_not_excluded(app):
            return app not in excludes

        candidates = {**self.scanned_apps, **self.all_instances()}
        return {
            app_name: app
            for app_name, app in candidates.items()
            if is_included(app_name) and is_not_excluded(app_name)
        }

    def _includes_with_instances(self) -> set[str]:
        """config.includes, expanded so naming an app or one of its instances pulls in the other."""
        includes = set(self.config.includes)
        if not includes:
            return includes
        for instance in self.all_instances().values():
            if instance.parent_app.name in includes or instance.name in includes:
                includes.add(instance.parent_app.name)
                includes.add(instance.name)
        return includes

    def all_dependencies(self):
        """Every soft and hard dependency reachable from the entrypoint apps."""
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

    def all_buildable_tasks(self):
        tasks = {}
        for app in self.scanned_apps.values():
            tasks.update(app._tasks)
        return tasks

    def all_source_images(self) -> dict[str, str]:
        """Every externally-sourced image: Dockerfile ARGs plus the source_images overrides."""
        images: dict[str, str] = {}
        for app in self.involved_apps:
            if isinstance(app, str):
                continue
            images.update(app.dockerfile.base_images)
        for base_image in self.base_images.values():
            images.update(base_image.dockerfile.base_images)
        images.update(self.all_values().get("source_images") or {})
        return images

    def _combined_dependencies(self, entity: CHApp | CHBaseImage | CHAppTask):
        """An entity's explicit build dependencies plus the ones guessed from its Dockerfile."""
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
        """Whether a task belongs to an app that isn't actually being deployed."""
        if self.config.manage_task_images or not isinstance(dependency, CHAppTask):
            return False
        return not dependency.app.is_involved

    def all_build_dependencies(self, already_covered=()):
        """Every build dependency reachable from the involved apps, transitively."""
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

    def _hashable_entities(self) -> dict[str, CHApp | CHBaseImage | CHAppTask]:
        """Every entity whose image needs a content-hash tag."""
        entities: dict[str, CHApp | CHBaseImage | CHAppTask] = {}
        for app in self._concrete_involved_apps:
            if app.is_buildable:
                entities[app.name] = app
            entities.update({t.name: t for t in app.buildable_tasks})
        entities.update(self.all_build_dependencies())
        # Left untagged, a test image resolves to `latest`, which already exists
        # in the registry, so a changed test would never trigger a rebuild.
        entities.update(self.test_images)
        return entities

    @lru_cache
    def _content_hash_tags(self) -> dict[str, str]:
        """Content-hash tags per entity, folding in each dependency's own hash; cycle-safe."""
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

    def qualify_image(self, entity: CHApp | CHBaseImage | CHAppTask) -> str:
        qualified = self.qualify(entity.image_name)
        if self._use_content_hash_tag:
            tag = self._content_hash_tags().get(entity.name)
        else:
            tag = self.config.tag
        return f"{qualified}:{tag}" if tag else qualified

    def all_task_images(self) -> dict[str, str]:
        """Qualified images for every build dependency and task, deployed or not."""
        already_deployed = tuple(app.name for app in self._concrete_involved_apps)
        images = {
            name: self.qualify_image(dependency)
            for name, dependency in self.all_build_dependencies(
                already_deployed
            ).items()
        }
        for app in self._concrete_involved_apps:
            images.update(app.task_images)
        return images

    @lru_cache
    def all_values(self):
        """Every involved app's values merged under the project's own defaults and overrides."""
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

    def build_final_helm_values(self, write_on_disk=True) -> HarnessMainConfig:
        """Assembles the final Helm values for every involved app and the project as a whole."""
        involved_apps = {app.name: app for app in self._concrete_involved_apps}
        values = self.all_values()
        apps = {
            name: _finalize_app_values(
                name,
                value,
                involved_apps[name].buildable_image,
                involved_apps[name].task_images,
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

        source_images = self.all_source_images()

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
        final_allvalues.setdefault("namespace", "")
        if self.config.tag:
            final_allvalues["tag"] = self.config.tag
        registry = dict(project_values.get("registry") or {})
        if self.config.local:
            registry["secret"] = None
        if self.config.registry:
            registry["name"] = self.config.registry
        if self.config.registry_secret_name:
            if not isinstance(registry.get("secret"), dict):
                registry["secret"] = {}
            registry["secret"]["name"] = self.config.registry_secret_name
        if registry:
            if not registry.get("name"):
                registry["name"] = self.config.registry
            final_allvalues["registry"] = registry

        for warning in self.validate():
            logging.warning(warning)

        helm_values = HarnessMainConfig.from_dict(final_allvalues)
        helm_values._ch_project = self

        if write_on_disk:
            CHValues.write_on_disk(
                Path(self.config.output_path) / "helm" / "values.yaml",
                helm_values.to_dict(),
            )

        return helm_values

    def validate(self) -> list[str]:
        """Non-fatal deployment warnings (nfs/use_services issues); raises on invalid secrets."""
        warnings: list[str] = []
        deployed = {app.name for app in self._concrete_involved_apps}
        for app in self._concrete_involved_apps:
            secrets = app.secrets
            if not isinstance(secrets, dict):
                raise ValuesValidationError(
                    f"Bad secrets specified for application {app.name}: expected a map of secret definitions"
                )
            for name, definition in secrets.items():
                error = secret_definition_error(definition)
                if error:
                    raise ValuesValidationError(
                        f"Bad definition for secret {name} of application {app.name}: {error}"
                    )

            volume = resolve_path(app.harness_config, "deployment.volume") or {}
            if volume.get("usenfs"):
                if volume.get("storageClass"):
                    warnings.append(
                        f"Volume {volume.get('name')} of application {app.name} sets usenfs and storageClass "
                        f"{volume['storageClass']}: the nfs server storage class prevails."
                    )
                if volume.get("writeMany") is False:
                    warnings.append(
                        f"Volume {volume.get('name')} of application {app.name} sets usenfs and writeMany false: "
                        "nfs volumes are always mounted ReadWriteMany."
                    )

            use_services = resolve_path(app.harness_config, "use_services") or []
            not_found = {
                s["name"] for s in use_services if s.get("name") not in deployed
            }
            if not_found:
                warnings.append(
                    f"Service proxy (use_services) dependencies for application {app.name} are not deployed: "
                    f"{','.join(not_found)}. Proxies to these services will not be created."
                )
        return warnings


@dataclass
class CHDeployConfig:
    """Deployment-wide configuration options."""

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
    chart_name: str | None = field(default=None, kw_only=True)
    chart_version: str | None = field(default=None, kw_only=True)
    app_version: str | None = field(default=None, kw_only=True)

    @property
    def envs(self) -> list[str]:
        if not self.env:
            return []
        return [self.env] if isinstance(self.env, str) else list(self.env)
