"""CHSkaffoldBuild: deployment/skaffold-build.yaml, the images a CI run still has to build."""

import os
import subprocess
from pathlib import Path

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain
from ruamel.yaml import YAML
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig, ci
from ch_cli_tools.api import create_helm_chart
from ch_cli_tools.skaffold import buildx_command, tag_template


def _project(tmp_path, include, tag=None):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path / "deployment",
        include=include,
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag=tag,
        registry="reg",
    )
    return values._ch_project


def _names(project):
    return [*ci.build_entities(project), *ci.test_runner_images(project)]


def _existing(project, *missing):
    """The `image_tag_env` of a registry holding every image but the missing ones."""
    return {
        ci.tag_variable(name) + ("_NEW" if name in missing else "_EXISTS"): "1"
        for name in _names(project)
    }


def _artifacts(plan):
    return {artifact["image"]: artifact for artifact in plan["build"]["artifacts"]}


def test_only_the_missing_images_are_built(tmp_path):
    project = _project(tmp_path, ["samples", "myapp"])
    plan = project.skaffold_build.generate(
        _existing(project, "myapp", "cloudharness-flask"), write_on_disk=False
    )
    artifacts = _artifacts(plan)
    myapp, flask = "reg/testprojectname/myapp", "reg/testprojectname/cloudharness-flask"
    assert set(artifacts) == {myapp, flask}
    assert plan["build"]["local"] == {"push": True, "concurrency": 0}

    # a base image built in the same run is required, so skaffold builds it first...
    assert artifacts[myapp]["requires"] == [{"image": flask, "alias": "CLOUDHARNESS_FLASK"}]
    # ...while one already in the registry is only pulled, by its tag
    assert "requires" not in artifacts[flask]
    base = project.qualify_image(project.base_images["cloudharness-base"])
    assert f"--build-arg CLOUDHARNESS_BASE={base}" in artifacts[flask]["custom"]["buildCommand"]

    # every image is tagged with the tag the helm chart deploys (here, its content hash)
    flask_reference = project.qualify_image(project.base_images["cloudharness-flask"])
    assert f"--build-arg CLOUDHARNESS_FLASK={flask_reference}" in artifacts[myapp]["custom"]["buildCommand"]
    template = plan["build"]["tagPolicy"]["envTemplate"]["template"]
    for image, entity in ((myapp, project["myapp"]), (flask, project.base_images["cloudharness-flask"])):
        tag = ci.ImageReference.parse(project.qualify_image(entity)).tag
        assert len(tag) == 40, "a content hash"
        assert f'"{image}" "{tag}"' in template


def test_build_command(tmp_path):
    project = _project(tmp_path, ["myapp"])
    plan = project.skaffold_build.generate(_existing(project, "myapp"), write_on_disk=False)
    command = _artifacts(plan)["reg/testprojectname/myapp"]["custom"]["buildCommand"]

    assert command.startswith("docker buildx build --push --file dev.Dockerfile ")
    assert '--tag "$IMAGE"' in command
    assert "${CH_BRANCH_TAG:+--tag reg/testprojectname/myapp:$CH_BRANCH_TAG}" in command
    assert "--build-arg NOCACHE " in command
    assert "--cache-from type=registry,ref=reg/testprojectname/myapp:buildcache " in command
    assert command.endswith(
        " --cache-to type=registry,ref=reg/testprojectname/myapp:buildcache,mode=max ."
    )
    assert ":latest" not in command, "only the test runner images are tagged latest"


def test_contexts_are_relative_to_the_project_root(tmp_path):
    # skaffold resolves the contexts from the directory it runs in: the workflow runs it from the root
    project = _project(tmp_path, ["samples", "myapp"])
    plan = project.skaffold_build.generate({}, write_on_disk=False)
    artifacts = _artifacts(plan)

    def context(image):
        return (project.root / artifacts[f"reg/testprojectname/{image}"]["context"]).resolve()

    assert context("myapp") == (RESOURCES / "applications" / "myapp").resolve()
    assert context("sampleapp") == (CLOUDHARNESS_ROOT / "applications" / "samples").resolve()
    # the project overrides cloud-harness' base image: built from the context merged across layers
    assert context("cloudharness-base") == (RESOURCES / ".overrides" / "cloudharness-base").resolve()
    assert artifacts["reg/testprojectname/myapp"]["context"] == "applications/myapp"


def test_test_runner_images_get_the_latest_tag(tmp_path):
    project = _project(tmp_path, ["samples"], tag="1")
    artifacts = _artifacts(project.skaffold_build.generate({}, write_on_disk=False))
    for name in ("test-api", "test-e2e"):
        command = artifacts[f"reg/testprojectname/{name}"]["custom"]["buildCommand"]
        assert f"--tag reg/testprojectname/{name}:latest" in command
    assert '"reg/testprojectname/test-api" "1"' in tag_template({"reg/testprojectname/test-api": "1"})

    # no app runs API/E2E tests: no test runner image
    project = _project(tmp_path, ["myapp"], tag="1")
    artifacts = _artifacts(project.skaffold_build.generate({}, write_on_disk=False))
    assert not [image for image in artifacts if "/test-" in image]


def test_nothing_to_build(tmp_path):
    project = _project(tmp_path, ["samples", "myapp"], tag="1")
    plan = project.skaffold_build.generate(_existing(project), write_on_disk=False)
    assert plan["build"]["artifacts"] == []
    assert plan["build"]["tagPolicy"]["envTemplate"]["template"] == "{{ index (dict ) .IMAGE_NAME }}"


def test_generate_writes_deployment_skaffold_build(tmp_path):
    write_tree_from_yaml(
        tmp_path,
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
    project = chain(
        CLOUDHARNESS_ROOT,
        tmp_path,
        config=CHDeployConfig(env="dev", registry="reg", tag="1", output_path=str(tmp_path / "deployment")),
    )
    project.skaffold_build.generate({"MYAPP_TAG_EXISTS": "1"})

    plan = YAML(typ="safe").load((tmp_path / "deployment" / "skaffold-build.yaml").read_text())
    assert plan["apiVersion"].startswith("skaffold/")
    assert plan["kind"] == "Config"
    assert "reg/testproj/myapp" not in _artifacts(plan), "its tag exists"
    assert "reg/testproj/cloudharness-base" in _artifacts(plan)


def test_build_command_shell_words(tmp_path):
    # the command runs through `sh -c`: check the words docker gets
    fake = tmp_path / "bin" / "docker"
    fake.parent.mkdir()
    fake.write_text('#!/bin/sh\nfor arg in "$@"; do echo "$arg"; done\n')
    fake.chmod(0o755)
    command = buildx_command("reg/x", "my dir/Dockerfile", {"A": "b c", "B": "$HOME"}, ("latest",))

    def words(**env):
        result = subprocess.run(
            ["sh", "-c", command],
            env={"PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}", "IMAGE": "reg/x:h1", **env},
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.splitlines()

    args = words(CH_BRANCH_TAG="feature-1")
    assert args[:5] == ["buildx", "build", "--push", "--file", "my dir/Dockerfile"]
    assert args[5:11] == ["--tag", "reg/x:h1", "--tag", "reg/x:latest", "--tag", "reg/x:feature-1"]
    assert "A=b c" in args and "B=$HOME" in args, "build args are passed literally"
    assert args[-1] == "."
    assert "reg/x:feature-1" not in words(), "no branch tag outside CI"
    assert Path(fake).exists()
