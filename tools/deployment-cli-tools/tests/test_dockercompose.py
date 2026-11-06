"""ch_cli_tools.dockercompose generator tests. Exercises the real `helm`
binary (used as a template engine, see dockercompose.py's module docstring)
against a minimal throwaway compose chart - see test_model.py in this folder for
the structural/model tests the values computation itself builds on.
"""

import shutil
import subprocess
from io import StringIO

import pytest
from conftest import CLOUDHARNESS_ROOT, RESOURCES
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig, CHProject
from ch_cli_tools.api import create_docker_compose_configuration
from ch_cli_tools.utils import get_yaml_parser

HELM_IS_INSTALLED = shutil.which("helm") is not None

MINIMAL_COMPOSE_CHART = """
    deployment-configuration:
      values-template.yaml: |
        name: testproj
        mainapp: myapp
      compose:
        Chart.yaml: |
          apiVersion: v2
          name: testproj
          version: 0.1.0
        values.yaml: "{}"
        templates:
          main.yaml: |
            apiVersion: v1
            kind: ConfigMap
            metadata:
              name: main
            data:
              hello: world
            ---
            cloudharness-metadata:
              path: embedded/secret.txt
            data: embedded-content
    applications:
      myapp:
        Dockerfile: |
          FROM scratch
        deploy:
          templates-compose:
            myapp.yaml: |
              apiVersion: v1
              kind: ConfigMap
              metadata:
                name: myapp-compose
          templates:
            _helper.tpl: |
              {{/* a helper */}}
"""


def _compose_project(tmp_path, **config_kwargs):
    write_tree_from_yaml(tmp_path, MINIMAL_COMPOSE_CHART)
    config_kwargs.setdefault("output_path", str(tmp_path / "deployment"))
    return CHProject(tmp_path, config=CHDeployConfig(**config_kwargs))


def test_generate_writes_values_and_secrets_stripped_allvalues(tmp_path):
    project = _compose_project(tmp_path)
    project.docker_compose.generate()

    dest = tmp_path / "deployment" / "compose"
    assert (dest / "values.yaml").exists()

    import yaml

    allvalues = yaml.safe_load((dest / "allvalues.yaml").read_text())
    assert allvalues["apps"]["myapp"]["harness"]["secrets"] == {}


def test_generate_uses_templates_compose_and_falls_back_to_regular_helpers(tmp_path):
    project = _compose_project(tmp_path)
    project.docker_compose.generate()

    app_templates = tmp_path / "deployment" / "compose" / "templates" / "myapp"
    assert (app_templates / "myapp.yaml").exists()
    assert (app_templates / "_helper.tpl").exists()


def test_generate_renders_docker_compose_above_output_path_and_splits_metadata(
    tmp_path,
):
    project = _compose_project(tmp_path)
    project.docker_compose.generate()

    compose_file = tmp_path / "docker-compose.yaml"
    content = compose_file.read_text()
    assert "cloudharness-metadata" not in content
    assert content.strip()

    embedded = tmp_path / "deployment" / "compose" / "embedded" / "secret.txt"
    assert embedded.read_text() == "embedded-content"


def test_generate_merges_compose_chart_across_base_layer(tmp_path):
    base_root = tmp_path / "base"
    top_root = tmp_path / "top"
    write_tree_from_yaml(base_root, MINIMAL_COMPOSE_CHART)
    write_tree_from_yaml(
        top_root,
        """
        deployment-configuration:
          values-template.yaml: |
            name: testproj
            mainapp: myapp
        applications:
          myapp:
            Dockerfile: |
              FROM scratch
        """,
    )

    config = CHDeployConfig(output_path=str(top_root / "deployment"))
    project = CHProject(base_root, config=config)
    project = CHProject(top_root, base=project, config=config)
    project.docker_compose.generate()

    dest = top_root / "deployment" / "compose"
    assert (dest / "Chart.yaml").exists()
    assert (dest / "templates" / "main.yaml").exists()


def test_compose_gatekeeper_native_configuration_rendering(tmp_path):
    """Exercises the real production compose chart's gatekeeper template, not the
    synthetic one above - a values-dict assertion can't tell whether tls/per-app
    overrides actually reach the rendered proxy.yml."""
    out_folder = tmp_path / "test_compose_gatekeeper_native_configuration"
    create_docker_compose_configuration(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        include=["samples"],
        domain="my.local",
        local=False,
        tls=True,
    )

    compose_path = out_folder / "compose"
    values_path = compose_path / "values.yaml"
    yaml = get_yaml_parser()
    with values_path.open() as values_file:
        values = yaml.load(values_file)

    values["apps"]["samples"]["harness"]["proxy"]["gatekeeper"]["configuration"] = {
        "same-site-cookie": "None",
        "enable-pkce": False,
        "http-only-cookie": True,
        "cors-exposed-headers": ["X-Request-ID", "X-Trace-ID"],
    }
    values["proxy"]["gatekeeper"]["configuration"] = {
        "same-site-cookie": "Strict",
        "enable-pkce": True,
        "max-token-size": 65536,
    }

    def render_proxy_config():
        with values_path.open("w") as values_file:
            yaml.dump(values, values_file)
        completed = subprocess.run(
            ["helm", "template", str(compose_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        with StringIO(completed.stdout) as stream:
            documents = list(yaml.load_all(stream))
        for document in documents:
            metadata = (document or {}).get("cloudharness-metadata", {})
            if metadata.get("path") == "resources/generated/samples-gk/proxy.yml":
                return yaml.load(document["data"])
        raise AssertionError(
            "Could not find the samples Gatekeeper proxy configuration"
        )

    tls_config = render_proxy_config()
    assert tls_config["secure-cookie"] is True
    assert tls_config["same-site-cookie"] == "None"
    assert tls_config["enable-pkce"] is False
    assert tls_config["http-only-cookie"] is True
    assert tls_config["max-token-size"] == 65536
    assert tls_config["cors-exposed-headers"] == ["X-Request-ID", "X-Trace-ID"]

    values["tls"] = False
    non_tls_config = render_proxy_config()
    assert non_tls_config["secure-cookie"] is False
    assert non_tls_config["same-site-cookie"] == "Lax"
    assert non_tls_config["enable-pkce"] is False
    assert non_tls_config["max-token-size"] == 65536

    values["tls"] = True
    values["apps"]["samples"]["harness"]["proxy"]["gatekeeper"]["configuration"].pop(
        "same-site-cookie"
    )
    inherited_config = render_proxy_config()
    assert inherited_config["same-site-cookie"] == "Strict"
    assert inherited_config["enable-pkce"] is False


@pytest.mark.skipif(not HELM_IS_INSTALLED, reason="helm is not installed")
def test_compose_secrets_use_local_defaults(tmp_path):
    """Secret managers are not available locally: compose falls back to the secret
    defaults - the values dict always strips secrets to {} (see
    test_generate_writes_values_and_secrets_stripped_allvalues above), so only the real
    rendered compose chart can confirm local defaults actually land on disk."""
    out_folder = tmp_path / "test_compose_secrets_use_local_defaults"
    create_docker_compose_configuration(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        include=["myapp"],
        exclude=["events", "legacy"],
        domain="my.local",
        namespace="test",
        env="secrets",
        local=False,
        tag="1",
        registry="reg",
    )

    generated = out_folder / "compose" / "resources" / "generated" / "auth"
    assert (generated / "plainSecret").read_text() == "a value"
    assert (generated / "richSecret").read_text() == "a local value"
    # nothing is known locally about an unmanaged secret: a random value is generated
    assert len((generated / "unmanagedSecret").read_text()) == 20
