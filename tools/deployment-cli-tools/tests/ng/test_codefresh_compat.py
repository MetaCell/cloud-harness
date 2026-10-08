# NG-COMPAT-TODO: retargeted at ch_cli_tools.ng.api.create_helm_chart/
# create_codefresh_deployment_scripts instead of the legacy ch_cli_tools.helm/
# ch_cli_tools.codefresh ones (ported from tests/test_codefresh.py). No
# preprocess_build_overrides() call - merging an overridden app/base-image's
# directory across layers happens transparently inside CHCodefresh.generate(),
# via CHContext.resolve_for_build(), the same mechanism create_skaffold_configuration
# already relies on.
#
# Scope of this file: the per-app/task/base-image build steps (including their
# dependency/source-image build_arguments), the unit test steps, and git-
# dependency clone steps, all landing inside the template's pre-declared
# containers (steps.build_application_images.steps / steps.tests_unit.steps /
# steps.post_main_clone.steps). Everything else legacy's
# create_codefresh_deployment_scripts also computes - api/e2e test steps,
# parallel-step batching into build_application_images_N, stage ordering,
# secrets/db-connect-string/registry-secret wiring into the deployment step,
# rollout-wait commands - is not generated yet, so none of that is asserted
# here.
from ch_cli_tools.ng.api import create_helm_chart, create_codefresh_deployment_scripts
from conftest import CLOUDHARNESS_ROOT, RESOURCES


def test_create_codefresh_configuration_build_steps(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["samples", "myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    # Template scaffolding (stages, main_clone, deployment, ...) survives untouched.
    assert cf["steps"]["main_clone"]["type"] == "git-clone"

    steps = cf["steps"]["build_application_images"]["steps"]

    # myapp: own Dockerfile, env-specific dev.Dockerfile preferred, project name
    # ("testprojectname") overriding the image path.
    myapp_step = steps["myapp"]
    assert myapp_step["dockerfile"] == "dev.Dockerfile"
    assert "testprojectname/" in myapp_step["image_name"]

    # cloudharness-base: overridden by RESOURCES, so it must build from the merged
    # .overrides directory, not straight from CLOUDHARNESS_ROOT's own tree - same
    # cross-layer merge CHSkaffold already relies on for its own artifacts.
    base_step = steps["cloudharness-base"]
    assert ".overrides" in base_step["working_directory"]
    assert base_step["dockerfile"] == "infrastructure/base-images/cloudharness-base/Dockerfile"
    assert "testprojectname/" in base_step["image_name"]

    # my-common: a common-image local to RESOURCES, never overridden - builds
    # straight from its own directory, dockerfile name alone (context == its own dir).
    common_step = steps["my-common"]
    assert common_step["dockerfile"] == "Dockerfile"
    assert common_step["working_directory"].endswith("infrastructure/common-images/my-common")

    # myapp's own task gets its own build step too, alongside the app.
    assert "myapp-mytask" in steps


def test_create_codefresh_configuration_build_arguments(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    steps = cf["steps"]["build_application_images"]["steps"]
    myapp_args = dict(arg.split("=", 1) for arg in steps["myapp"]["build_arguments"])

    # harness.dependencies.build (cloudharness-flask, plus my-common added by
    # values-dev.yaml) resolve to the already-qualified image this same
    # pipeline is building for them, not a bare/unqualified name.
    assert myapp_args["CLOUDHARNESS_FLASK"] == "reg/testprojectname/cloudharness-flask"
    assert myapp_args["MY_COMMON"] == "reg/testprojectname/my-common"

    # Globally ARG-pinned source images (from real cloud-harness base images'
    # own Dockerfiles) are merged in too - the same value on every build step,
    # even one (cloudharness-base) with no dependencies of its own.
    assert myapp_args["NODE"] == "node:22-alpine"
    base_args = dict(
        arg.split("=", 1) for arg in steps["cloudharness-base"]["build_arguments"]
    )
    assert base_args["NODE"] == myapp_args["NODE"]


def test_create_codefresh_configuration_unit_tests(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    unit_steps = cf["steps"]["tests_unit"]["steps"]
    assert "myapp_ut" in unit_steps

    step = unit_steps["myapp_ut"]
    assert step["commands"] == ["tox", 'echo "hello"']
    # NG-COMPAT-TODO: legacy's image is a Codefresh template-variable reference
    # (image_tag_with_variables -> "${{REGISTRY}}/testprojectname/myapp:${{MYAPP_TAG}}"),
    # tied to its own CF-variable-based tagging scheme. ng has no such scheme -
    # every generator (skaffold, this one) just qualifies the already-resolved
    # image reference directly, consistent across the whole ng model.
    assert step["image"] == "reg/testprojectname/myapp"


def test_create_codefresh_configuration_no_unit_tests_when_not_included(tmp_path):
    """An app with no test.unit.commands gets no unit test step at all."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["accounts"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    unit_steps = cf["steps"]["tests_unit"]["steps"]
    assert "accounts_ut" not in unit_steps


def test_create_codefresh_configuration_git_clone_steps(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    clone_steps = cf["steps"]["post_main_clone"]["steps"]

    # Template-provided clone step survives untouched alongside the computed ones.
    assert clone_steps["clone_cloud_harness"]["type"] == "git-clone"

    # myapp declares two harness.dependencies.git entries (tests/resources/
    # applications/myapp/deploy/values.yaml): one with no `path` override, one
    # with path="myrepo".
    no_path_step = clone_steps["clone_b_git_master_myapp"]
    assert no_path_step["repo"] == "https://github.com/a/b.git"
    assert no_path_step["revision"] == "master"
    assert no_path_step["git"] == "github"
    assert no_path_step["working_directory"].endswith("applications/myapp/dependencies")

    with_path_step = clone_steps["clone_d_git_v1_0_0_myapp"]
    assert with_path_step["repo"] == "https://github.com/c/d.git"
    assert with_path_step["revision"] == "v1.0.0"
    assert with_path_step["working_directory"].endswith(
        "applications/myapp/dependencies/myrepo"
    )


def test_create_codefresh_configuration_no_git_clone_steps_when_no_git_dependencies(
    tmp_path,
):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["accounts"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    clone_steps = cf["steps"]["post_main_clone"]["steps"]
    # Only the static template step is present - accounts has no git dependencies.
    assert list(clone_steps.keys()) == ["clone_cloud_harness"]
