"""ch_cli_tools.ng.dockercompose generator tests. Exercises the real `helm`
binary (used as a template engine, see dockercompose.py's module docstring)
against a minimal throwaway compose chart - see test_ng.py in this folder for
the structural/model tests the values computation itself builds on.
"""

from test_util_ng import write_tree_from_yaml

from ch_cli_tools.ng import CHDeployConfig, CHProject

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
