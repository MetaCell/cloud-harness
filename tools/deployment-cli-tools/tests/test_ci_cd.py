"""`harness-generate ci-cd`: one pipeline per CI provider and environment the project has a template for."""

import logging

import pytest
from conftest import CLOUDHARNESS_ROOT
from ruamel.yaml import YAML
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig
from ch_cli_tools.api import generate_ci_cd
from ch_cli_tools.ci import pipeline_file_name, template_environments

PROJECT = """
    deployment-configuration:
      values-template.yaml: |
        name: testproj
        mainapp: myapp
      github-template-dev.yaml: ""
      github-template-test.yaml: ""
      codefresh-template-test.yaml: ""
    applications:
      myapp:
        Dockerfile: |
          FROM scratch
"""


def _load(path):
    return YAML(typ="safe").load(path.read_text())


@pytest.mark.parametrize(
    "config, suffix, expected",
    [
        (CHDeployConfig(env="dev"), None, "ci--all--dev.yaml"),
        (CHDeployConfig(env="dev", includes=["samples"]), None, "ci--samples--dev.yaml"),
        (CHDeployConfig(env=["research", "dev"], includes=["a", "b"]), None, "ci--a-b--research-dev.yaml"),
        (CHDeployConfig(env="dev", includes=["a", "b"], pipeline="ab"), None, "ci--ab--dev.yaml"),
        (CHDeployConfig(env="dev", includes=["samples"]), "promote", "ci--samples--promote.yaml"),
        (CHDeployConfig(), None, "ci--all.yaml"),
    ],
)
def test_pipeline_file_name(config, suffix, expected):
    assert pipeline_file_name(config, suffix) == expected


def test_pipeline_name_must_be_a_file_name():
    with pytest.raises(ValueError, match="Invalid pipeline name"):
        pipeline_file_name(CHDeployConfig(env="dev", pipeline="a/b"))


def test_template_environments(tmp_path, caplog):
    for name in (
        "github-template.yaml",
        "github-template-dev.yaml",
        "github-template-test.yaml",
        "github-template-test-mnp.yaml",
        "codefresh-build-template.yaml",
    ):
        (tmp_path / name).write_text("")
    with caplog.at_level(logging.WARNING):
        assert template_environments(tmp_path, "github-template") == ["dev", "test"]
    # `-e test-mnp` merges the test and mnp templates, never reads github-template-test-mnp.yaml
    assert "github-template-test-mnp.yaml" in caplog.text
    assert template_environments(tmp_path, "codefresh-template") == []


def test_only_the_project_templates_make_pipelines(tmp_path):
    write_tree_from_yaml(tmp_path, PROJECT)
    written = generate_ci_cd([CLOUDHARNESS_ROOT, tmp_path], CHDeployConfig(includes=["myapp"]))

    workflows = tmp_path / ".github" / "workflows"
    # cloud-harness' stage and prod templates are not inherited: the project has no file for them
    assert written == [
        tmp_path / "deployment" / "ci--myapp--test.yaml",
        workflows / "ci--myapp--dev.yaml",
        workflows / "ci--myapp--promote.yaml",
        workflows / "ci--myapp--test.yaml",
    ]
    assert sorted(path.name for path in workflows.iterdir()) == [
        "ci--myapp--dev.yaml",
        "ci--myapp--promote.yaml",
        "ci--myapp--test.yaml",
    ]

    # the empty project templates inherit everything from cloud-harness'
    dev = _load(workflows / "ci--myapp--dev.yaml")
    assert dev["name"] == "CloudHarness dev" and dev["on"]["push"]["branches"] == ["develop"]
    prepare = next(step for step in dev["jobs"]["prepare"]["steps"] if step.get("id") == "images")
    assert "-e dev " in prepare["run"] and "$HELM_META_ARGS -i myapp\n" in prepare["run"]
    # promote runs of the workflow written with it
    promote = (workflows / "ci--myapp--promote.yaml").read_text()
    assert "--workflow ci--myapp--dev.yaml " in promote
    assert (workflows / "ci--myapp--dev.yaml").read_text().startswith("name: CloudHarness dev\n")

    codefresh = _load(tmp_path / "deployment" / "ci--myapp--test.yaml")
    assert any("-e test " in command for command in codefresh["steps"]["prepare_deployment"]["commands"])


def test_requested_environments_and_combinations(tmp_path, caplog):
    write_tree_from_yaml(tmp_path, PROJECT)
    with caplog.at_level(logging.WARNING):
        written = generate_ci_cd(
            [CLOUDHARNESS_ROOT, tmp_path],
            CHDeployConfig(includes=["myapp"], pipeline="mine"),
            envs=["test-dev", "stage"],
        )

    workflows = tmp_path / ".github" / "workflows"
    assert written == [workflows / "ci--mine--test-dev.yaml", workflows / "ci--mine--promote.yaml"]
    workflow = _load(workflows / "ci--mine--test-dev.yaml")
    # test-dev merges the test then the dev template, triggers included
    assert workflow["name"] == "CloudHarness test-dev"
    assert set(workflow["on"]) == {"pull_request", "push", "workflow_dispatch"}
    assert "--workflow ci--mine--test-dev.yaml " in (workflows / "ci--mine--promote.yaml").read_text()
    # a combination needs a project template for each of its environments
    assert "codefresh-template-dev.yaml" in caplog.text
    assert "github-template-stage.yaml" in caplog.text
    assert not (tmp_path / "deployment").exists()


def test_no_project_template_means_no_pipeline(tmp_path):
    write_tree_from_yaml(tmp_path, PROJECT)
    for template in (tmp_path / "deployment-configuration").glob("*-template-*.yaml"):
        template.unlink()
    assert generate_ci_cd([CLOUDHARNESS_ROOT, tmp_path], CHDeployConfig()) == []
    assert not (tmp_path / ".github").exists()
