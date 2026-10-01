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

from dataclasses import replace

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
    # secured/tls/name/chart_version/app_version: accepted for signature
    # compat, not wired yet - see ng/api.py's module docstring and
    # CHProject.build_final_helm_values (secured_gatekeepers is hardcoded True,
    # no CHDeployConfig field for it yet; Chart.yaml metadata has no ng
    # generator yet).
    root_paths = list(root_paths)

    config_kwargs = dict(
        includes=list(include or []),
        excludes=list(exclude or []),
        registry=registry,
        tag=tag,
        local=local,
        namespace=namespace,
        registry_secret_name=registry_secret_name,
        output_path=output_path,
    )
    if env:
        config_kwargs["env"] = env
    if domain:
        config_kwargs["domain"] = domain

    config = CHDeployConfig(**config_kwargs)
    project = None
    for path in root_paths:  # lowest priority first, most specific last
        project = CHProject(path, base=project, config=config)
    assert project, "Couldn't build the project root representation"
    return project.build_final_helm_values()


def deploy(namespace, output_path="./deployment"):
    pass


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
    pass


# --- ch_cli_tools/configurationgenerator.py ---


def hosts_info(values):
    pass


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
    base_config = helm_values._ch_project.config
    config = replace(
        base_config,
        backend="compose" if backend_deploy == "docker-compose" else "helm",
        env=env if env is not None else base_config.env,
        manage_task_images=manage_task_images,
    )

    # builds the CHProject chain
    project = None
    for path in root_paths:  # lowest priority first, most specific last
        project = CHProject(path, base=project, config=config)

    assert project, "Couldn't build the project root representation"
    return project.skaffold.generate(output_path=output_path)


def create_vscode_debug_configuration(root_paths, helm_values):
    pass


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
    pass


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
    pass


def write_env_file(helm_values, filename, image_cache_endpoint_url=None):
    pass


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
    pass
