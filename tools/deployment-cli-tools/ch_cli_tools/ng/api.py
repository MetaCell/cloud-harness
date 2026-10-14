"""High-level, user/script-facing deployment generation entry points.

This is the surface `harness-deployment` (and any other script) actually calls
- one function per legacy top-level entry point in ch_cli_tools/{helm,
dockercompose,configurationgenerator,skaffold,tilt,codefresh,preprocessing,
migration,utils}.py. Signatures mirror the legacy ones so the existing tests
for each (tests/test_helm.py, tests/test_skaffold.py, etc.) can be retargeted
at these once implemented, instead of rewritten.

First pass: signatures only, `pass` bodies. Implementation comes later, backed
by CHProject/CHDeployConfig and the rest of the ng model instead of the legacy
ConfigurationGenerator/HarnessMainConfig machinery.
"""

import logging
import subprocess
from pathlib import Path

from ch_cli_tools.utils import get_cluster_ip  # type: ignore

from . import migration
from .model import CHDeployConfig, CHProject

# --- ch_cli_tools/helm.py ---


def create_helm_chart(
    root_paths,
    tag=None,
    registry="",
    local=True,
    domain=None,
    exclude=(),
    secured=True,
    output_path="./deployment",
    include=None,
    registry_secret_name=None,
    tls=True,
    env=None,
    namespace=None,
    name=None,
    chart_version=None,
    app_version=None,
):
    root_paths = list(root_paths)

    config_kwargs = {
        "includes": list(include or []),
        "excludes": list(exclude or []),
        "registry": registry,
        "tag": str(tag) if tag is not None else None,
        "local": local,
        "namespace": namespace,
        "registry_secret_name": registry_secret_name,
        "output_path": output_path,
        "tls": tls,
        "secured_gatekeepers": secured,
        "chart_name": name,
        "chart_version": chart_version,
        "app_version": app_version,
    }
    if env:
        config_kwargs["env"] = env
    if domain:
        config_kwargs["domain"] = domain

    config = CHDeployConfig(**config_kwargs)
    project = CHProject.init(root_paths, config=config)
    project.helm_chart.generate()
    return project.build_final_helm_values()


def deploy(namespace, output_path="./deployment"):
    helm_path = Path(output_path) / "helm"
    logging.info("Deploying helm chart %s", helm_path)
    subprocess.run("helm dependency update".split(), cwd=helm_path)
    subprocess.run(
        f"helm upgrade {namespace} {helm_path} -n {namespace} --install --reset-values".split()
    )


# --- ch_cli_tools/dockercompose.py ---


def create_docker_compose_configuration(
    root_paths,
    tag=None,
    registry="",
    local=True,
    domain=None,
    exclude=(),
    secured=True,
    output_path="./deployment",
    include=None,
    registry_secret_name=None,
    tls=True,
    env=None,
    namespace=None,
):
    root_paths = list(root_paths)

    config_kwargs = {
        "includes": list(include or []),
        "excludes": list(exclude or []),
        "registry": registry,
        "tag": str(tag) if tag is not None else None,
        "local": local,
        "namespace": namespace,
        "registry_secret_name": registry_secret_name,
        "output_path": output_path,
        "tls": tls,
        "secured_gatekeepers": secured,
        "backend": "compose",
    }
    if env:
        config_kwargs["env"] = env
    if domain:
        config_kwargs["domain"] = domain

    project = CHProject.init(root_paths, config=CHDeployConfig(**config_kwargs))
    project.docker_compose.generate()
    return project.build_final_helm_values()


# --- ch_cli_tools/configurationgenerator.py ---


def hosts_info(values):
    apps = [app for app in values.apps.values() if app.harness]

    subdomains = [app.harness.subdomain for app in apps if app.harness.subdomain] + [
        alias for app in apps if app.harness.aliases for alias in app.harness.aliases
    ]

    logging.info("\nTo run locally some apps, also those references may be needed")
    for app in apps:
        if not app.harness.service:
            continue
        service = app.harness.service
        print(
            f"kubectl port-forward -n {values.namespace} service/{service.name} "
            f"{service.port}:{service.port}"
        )

    hosts = [
        f"{app.harness.service.name}.{values.namespace}"
        for app in apps
        if app.harness.service
    ]
    print(f"127.0.0.1\t{' '.join(hosts)}")

    try:
        ip = get_cluster_ip(local=values.local)
    except Exception:
        logging.warning("Cannot get cluster ip")
        ip = "127.0.0.1"
    logging.info(
        "\nTo test locally, update your hosts file"
        + f"\n{ip}\t{values.domain + ' ' + ' '.join(sd + '.' + values.domain for sd in subdomains)}"
    )


# --- ch_cli_tools/skaffold.py ---
# create_skaffold_configuration's replacement already exists as
# ng.skaffold.CHSkaffold.generate() - this stub is only about matching the
# legacy call convention (root_paths/helm_values) so the old tests can drive it.


def create_skaffold_configuration(
    root_paths,
    helm_values,
    output_path=".",
    manage_task_images=True,
    backend_deploy=None,
    env=None,
):
    project = helm_values._ch_project
    project.config.backend = "compose" if backend_deploy == "docker-compose" else "helm"
    return project.skaffold.generate(output_path=output_path)


def create_vscode_debug_configuration(root_paths, helm_values):
    project = helm_values._ch_project
    return project.vscode_debug.generate()


# --- ch_cli_tools/tilt.py ---


def create_tilt_configuration(
    root_paths,
    helm_values,
    manage_task_images=True,
    output_path=".",
    name="",
    namespace="",
    domain="",
):
    # root_paths/manage_task_images/name/namespace/domain: accepted for
    # signature compat only - same reasoning as create_skaffold_configuration
    # above, the real CLI always passes the namespace/domain already baked
    # into helm_values's own project config, never a different one.
    project = helm_values._ch_project
    return project.tilt.generate(output_path=output_path)


# --- ch_cli_tools/codefresh.py ---


def create_codefresh_deployment_scripts(
    root_paths,
    envs=(),
    include=(),
    exclude=(),
    template_name=None,
    base_image_name=None,
    helm_values=None,
    save=True,
):
    project = helm_values._ch_project
    return project.codefresh.generate(write_on_disk=save)


def write_env_file(helm_values, filename, image_cache_endpoint_url=None):
    project = helm_values._ch_project
    return project.codefresh.write_env_file(filename, image_cache_endpoint_url)


# --- ch_cli_tools/preprocessing.py ---
# preprocess_build_overrides physically merges overlapping app/base-image
# directories across root_paths into one filesystem tree, so a Docker build
# context sees files from every root that touches that app, not just the one
# that owns the Dockerfile. Whether this is still needed depends on whether
# the ng model keeps allowing a root to contribute extra build-context files
# alongside a Dockerfile it doesn't own itself (CHApp.base only merges
# *values*, never the filesystem) - open question, not decided yet.


def preprocess_build_overrides(root_paths, helm_values, merge_build_path=None):
    pass


def generate_hash_based_image_tags(root_paths, helm_values, merge_build_path=None):
    pass


# --- ch_cli_tools/utils.py ---


def merge_app_directories(root_paths, destination) -> None:
    pass


# --- ch_cli_tools/migration.py ---


def perform_migration(base_root, accept_all=False):
    return migration.perform_migration(base_root, accept_all=accept_all)
