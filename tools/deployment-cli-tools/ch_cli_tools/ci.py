"""Provider-neutral pieces shared by the CI/CD generators (Codefresh, GitHub Actions).

Both pipelines skip the build of an image whose content-hash tag already exists
in the registry. The facts needed for that decision - the tag of every image the
deployment references and whether that tag is already published - can only be
known at pipeline run time, so they are computed by `harness-deployment
--write-env` inside the pipeline's prepare step and handed to the following
steps as `<IMAGE>_TAG` / `<IMAGE>_TAG_EXISTS` variables (`image_tag_env`).
"""

import logging
from dataclasses import dataclass

from ch_cli_tools.configuration.secrets import (
    is_cloudharness_managed,
    is_secret_config,
    secret_value,
)
from ch_cli_tools.utils import check_image_exists_in_registry  # type: ignore

from .model import KEY_APPS, KEY_TASK_IMAGES

logger = logging.getLogger(__name__)

FORCE_BUILD_ALL = "all"
DOCKER_HUB_REGISTRY = "docker.io"


def env_key(name: str) -> str:
    """The variable-name form of an image/app name: `my-app` -> `MY_APP`."""
    return name.replace("-", "_").upper()


def tag_variable(name: str) -> str:
    return f"{env_key(name)}_TAG"


def parse_force_build(value: str | None) -> tuple[str, ...]:
    """The `--force-build` CLI value: a comma-separated list of image names, or `all`."""
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def is_forced(name: str, force_build=()) -> bool:
    forced = set(force_build)
    return FORCE_BUILD_ALL in forced or name in forced


@dataclass(frozen=True)
class ImageReference:
    """A `[registry/]repository[:tag]` image reference split into its parts."""

    registry: str
    repository: str
    tag: str

    @classmethod
    def parse(cls, image: str) -> "ImageReference":
        name, tag = image, "latest"
        last_segment = image.rsplit("/", 1)[-1]
        if ":" in last_segment:
            name, tag = image.rsplit(":", 1)
        chunks = name.split("/")
        first = chunks[0]
        has_registry_host = len(chunks) > 1 and (
            "." in first or ":" in first or first == "localhost"
        )
        if has_registry_host:
            return cls(first, "/".join(chunks[1:]), tag)
        return cls(DOCKER_HUB_REGISTRY, name, tag)


def image_tag_env(project, image_cache_endpoint_url=None, force_build=()) -> dict[str, str]:
    """`<IMAGE>_TAG` plus `<IMAGE>_TAG_EXISTS` or `<IMAGE>_TAG_NEW` for every image of the deployment.

    Covers the apps (instances included), the task images (tasks and build
    dependencies) and the test runner images. A forced image is reported as new
    without asking the registry.
    """
    helm_values = project.build_final_helm_values(write_on_disk=False)
    env: dict[str, str] = {}

    def record(name: str, image: str) -> None:
        reference = ImageReference.parse(image)
        env[tag_variable(name)] = reference.tag
        exists = not is_forced(name, force_build) and check_image_exists_in_registry(
            reference.registry,
            reference.repository,
            reference.tag,
            endpoint_url=image_cache_endpoint_url,
        )
        env[tag_variable(name) + ("_EXISTS" if exists else "_NEW")] = "1"

    for app_name, app in helm_values.apps.items():
        if app.harness and app.harness.deployment.image:
            record(app_name, app.harness.deployment.image)

    for name, image in helm_values[KEY_TASK_IMAGES].items():
        record(name, image)

    for name, test_image in project.test_images.items():
        if not test_image.dockerfile.exists():
            continue
        record(name, project.qualify_image(test_image))

    return env


def write_env_file(path, env: dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(f"{key}={value}\n" for key, value in env.items())
    logger.info("Wrote %s", path)


def image_tag_names(project) -> list[str]:
    """The names `image_tag_env` reports on, in the same order, without touching the registry."""
    helm_values = project.build_final_helm_values(write_on_disk=False)
    names = [
        app_name
        for app_name, app in helm_values.apps.items()
        if app.harness and app.harness.deployment.image
    ]
    names.extend(helm_values[KEY_TASK_IMAGES])
    names.extend(
        name for name, image in project.test_images.items() if image.dockerfile.exists()
    )
    return names


def placeholder_values(project, pipeline_path) -> dict[str, str]:
    """Values for the `$ENV`, `$PARAMS` and `$PATHS` placeholders of a prepare command.

    `pipeline_path(layer_root)` renders one layer root the way the pipeline's
    checkout lays it out (cloud-harness is cloned into ./cloud-harness).
    """
    config = project.config
    params = [f"-i {inc}" for inc in config.includes] + [
        f"-ex {exc}" for exc in config.excludes
    ]
    paths = " ".join(
        str(pipeline_path(layer.root)) for layer in reversed(project.all_layers())
    )
    return {
        "ENV": "-".join(config.envs),
        "PARAMS": " ".join(params),
        "PATHS": paths,
    }


def app_domain(app, domain: str) -> str:
    """`https://<subdomain>.<domain>`, with `domain` typically a pipeline-variable reference."""
    return f"https://{app.harness_config.get('subdomain')}.{domain}"


def test_environment(app, app_domain_url: str) -> dict[str, str]:
    """Environment of the API/E2E test runner for an app: URL, main user credentials, test flags."""
    env: dict[str, str] = {"APP_URL": app_domain_url}
    users = app.harness_config.get("accounts", {}).get("users") or []
    if users:
        main_user = users[0]
        env["USERNAME"] = main_user.get("username")
        env["PASSWORD"] = main_user.get("password") or "test"
    e2e = app.test.e2e
    if not e2e.smoketest:
        env["SKIP_SMOKETEST"] = "true"
    if e2e.ignore_console_errors:
        env["IGNORE_CONSOLE_ERRORS"] = "true"
    if e2e.ignore_request_errors:
        env["IGNORE_REQUEST_ERRORS"] = "true"
    return env


def schemathesis_command(app, app_domain_url: str) -> str:
    api = app.test.api
    params = ["--base-url", app_domain_url]
    for check in api.checks:
        params += ["-c", check]
    params += api.run_params
    return " ".join(
        [
            "st",
            "--pre-run",
            "cloudharness_test.apitest_init",
            "run",
            "api/openapi.yaml",
            *params,
        ]
    )


def api_test_commands(app, app_domain_url: str) -> list[str]:
    commands = []
    if app.test.api.autotest:
        commands.append(schemathesis_command(app, app_domain_url))
    if (app.path / "test" / "api").exists():
        commands.append("pytest -v test/api")
    return commands


def api_test_url(app, domain: str) -> str | None:
    """The base URL of an app's API tests, or None when the app declares no server URL."""
    server_urls = app.openapi.server_urls
    if not server_urls:
        return None
    url = server_urls[-1]
    if "http" not in url:
        url = app_domain(app, domain) + url
    return url


def has_api_tests(app) -> bool:
    return bool(
        app.is_buildable and app.test.api.enabled and app.harness_config.get("subdomain")
    )


def has_e2e_tests(app) -> bool:
    return bool(
        app.is_buildable and app.test.e2e.enabled and app.harness_config.get("subdomain")
    )


def rollout_wait_commands(project) -> list[str]:
    """`kubectl rollout status` for every auto-deployed workload and gatekeeper, then a settle pause."""
    secured_gatekeepers = project.config.secured_gatekeepers
    commands = []
    for app in project.involved_apps:
        if isinstance(app, str):
            continue
        deployment = app.deployment_config
        if deployment.get("auto"):
            kind = "statefulset" if deployment.get("statefulset") else "deployment"
            name = deployment.get("name") or app.name
            commands.append(f"kubectl rollout status {kind}/{name}")
        if app.harness_config.get("secured") and secured_gatekeepers:
            # gatekeepers are always rendered as deployments
            subdomain = app.harness_config.get("subdomain")
            commands.append(f"kubectl rollout status deployment/{subdomain}-gk")
    if commands:
        commands.append("sleep 60")  # give the certificates time to settle
    return commands


@dataclass(frozen=True)
class HelmSecretValue:
    """A helm value the pipeline must supply from one of its own secret variables."""

    path: tuple[str, ...]  # helm value path, e.g. ("apps", "myapp", "harness", "secrets", "token")
    variable: str  # pipeline variable holding the value, e.g. TOKEN


def deployment_secret_values(project) -> list[HelmSecretValue]:
    """CloudHarness-managed secrets, auto-generated DB connect strings and the registry
    secret, each as the helm value path to set and the pipeline variable to take it from.

    Secrets handled by another manager, or whose value is already set, are left alone.
    Variable names follow the Codefresh convention: upper case, `_` doubled.
    """
    values = []
    for app in project.involved_apps:
        if isinstance(app, str):
            continue
        for secret, definition in app.secrets.items():
            if not is_cloudharness_managed(definition) or secret_value(definition) == "":
                continue
            path: tuple[str, ...] = (KEY_APPS, app.name, "harness", "secrets", secret)
            # the rich form nests the value under `default`
            if is_secret_config(definition):
                path += ("default",)
            values.append(HelmSecretValue(path, secret.replace("_", "__").upper()))
        if app.database.get("connect_string") == "":
            values.append(
                HelmSecretValue(
                    (KEY_APPS, app.name, "harness", "database", "connect_string"),
                    f"{env_key(app.name)}_DB_CONNECT_STRING",
                )
            )
    if project.config.registry_secret_name:
        values.append(HelmSecretValue(("registry", "secret", "value"), "K8S_SA_JSON"))
    return values
