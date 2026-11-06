"""CHSkaffoldCI: deployment/skaffold-ci.yaml, the images a CI run still has to build."""

import json
import os
import subprocess

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain
from ruamel.yaml import YAML
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig, ci
from ch_cli_tools.api import create_helm_chart
from ch_cli_tools.skaffold import buildx_command, tag_template, unit_test_command


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
    plan = project.skaffold_ci.generate(
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
    plan = project.skaffold_ci.generate(_existing(project, "myapp"), write_on_disk=False)
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
    plan = project.skaffold_ci.generate({}, write_on_disk=False)
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
    artifacts = _artifacts(project.skaffold_ci.generate({}, write_on_disk=False))
    for name in ("test-api", "test-e2e"):
        command = artifacts[f"reg/testprojectname/{name}"]["custom"]["buildCommand"]
        assert f"--tag reg/testprojectname/{name}:latest" in command
    assert '"reg/testprojectname/test-api" "1"' in tag_template({"reg/testprojectname/test-api": "1"})

    # no app runs API/E2E tests: no test runner image
    project = _project(tmp_path, ["myapp"], tag="1")
    artifacts = _artifacts(project.skaffold_ci.generate({}, write_on_disk=False))
    assert not [image for image in artifacts if "/test-" in image]


def test_nothing_to_build(tmp_path):
    project = _project(tmp_path, ["samples", "myapp"], tag="1")
    plan = project.skaffold_ci.generate(_existing(project), write_on_disk=False)
    assert plan["build"]["artifacts"] == []
    assert plan["build"]["tagPolicy"]["envTemplate"]["template"] == "{{ index (dict ) .IMAGE_NAME }}"


def test_unit_tests_cover_every_app(tmp_path):
    project = _project(tmp_path, ["samples", "myapp"])
    # nothing to build: the unit tests still run, against the images in the registry
    plan = project.skaffold_ci.generate(_existing(project), write_on_disk=False)
    assert plan["build"]["artifacts"] == []
    tests = {test["image"]: test["custom"] for test in plan["test"]}
    assert set(tests) == {"reg/testprojectname/myapp", "reg/testprojectname/sampleapp"}
    assert tests["reg/testprojectname/myapp"] == [
        {"command": 'docker run --rm "$IMAGE" sh -c \'set -e\ntox\necho "hello"\''}
    ]

    # `skaffold test --build-artifacts` takes every image's tag from skaffold-images.json
    images = {build["imageName"]: build["tag"] for build in project.skaffold_ci.images()["builds"]}
    assert images["reg/testprojectname/myapp"] == project.qualify_image(project["myapp"])
    assert set(tests) <= set(images)
    assert set(images) == {
        project.qualify(entity.image_name)
        for entity in {**ci.build_entities(project), **ci.test_runner_images(project)}.values()
    }


def test_deploy_installs_the_chart_and_waits_for_the_rollout(tmp_path):
    project = _project(tmp_path, ["samples", "myapp"])
    plan = project.skaffold_ci.generate(_existing(project), write_on_disk=False)
    # tolerateFailuresUntilDeadline needs a v4 schema
    assert plan["apiVersion"] == "skaffold/v4beta14"
    deploy = plan["deploy"]
    assert deploy["tolerateFailuresUntilDeadline"] is True
    assert deploy["statusCheckDeadlineSeconds"] == 900
    [release] = deploy["helm"]["releases"]
    assert release["name"] == release["namespace"] == "test"
    assert release["chartPath"] == "deployment/helm"
    assert release["createNamespace"] is True and release["skipBuildDependencies"] is True
    # secret values come from the files the pipeline writes, never from the file itself
    assert release["setFiles"]["apps.samples.harness.secrets.asecret"] == "~/.cloudharness/secrets/ASECRET"
    assert release["setFiles"]["apps.myapp.harness.database.connect_string"] == (
        "~/.cloudharness/secrets/MYAPP_DB_CONNECT_STRING"
    )


def test_generate_writes_deployment_skaffold_ci(tmp_path):
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
    project.skaffold_ci.generate({"MYAPP_TAG_EXISTS": "1"})

    plan = YAML(typ="safe").load((tmp_path / "deployment" / "skaffold-ci.yaml").read_text())
    assert plan["apiVersion"].startswith("skaffold/")
    assert plan["kind"] == "Config"
    # no namespace configured: the helm values' default one
    [release] = plan["deploy"]["helm"]["releases"]
    assert release["name"] == release["namespace"] == "ch"
    assert "reg/testproj/myapp" not in _artifacts(plan), "its tag exists"
    assert "reg/testproj/cloudharness-base" in _artifacts(plan)
    images = json.loads((tmp_path / "deployment" / "skaffold-images.json").read_text())
    assert {"imageName": "reg/testproj/myapp", "tag": "reg/testproj/myapp:1"} in images["builds"]


def test_shell_words(tmp_path):
    # the build and test commands run through `sh -c`: check the words docker gets
    fake = tmp_path / "bin" / "docker"
    fake.parent.mkdir()
    fake.write_text('#!/bin/sh\nfor arg in "$@"; do echo "$arg"; done\n')
    fake.chmod(0o755)

    def words(command, **env):
        result = subprocess.run(
            ["sh", "-c", command],
            env={"PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}", "IMAGE": "reg/x:h1", **env},
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.splitlines()

    build = buildx_command("reg/x", "my dir/Dockerfile", {"A": "b c", "B": "$HOME"}, ("latest",))
    args = words(build, CH_BRANCH_TAG="feature-1")
    assert args[:5] == ["buildx", "build", "--push", "--file", "my dir/Dockerfile"]
    assert args[5:11] == ["--tag", "reg/x:h1", "--tag", "reg/x:latest", "--tag", "reg/x:feature-1"]
    assert "A=b c" in args and "B=$HOME" in args, "build args are passed literally"
    assert args[-1] == "."
    assert "reg/x:feature-1" not in words(build), "no branch tag outside CI"

    # the unit tests run in the image's own shell, one container for all the commands
    args = words(unit_test_command(["tox", 'echo "a b" $HOME']))
    assert args[:5] == ["run", "--rm", "reg/x:h1", "sh", "-c"]
    assert "\n".join(args[5:]) == 'set -e\ntox\necho "a b" $HOME'
