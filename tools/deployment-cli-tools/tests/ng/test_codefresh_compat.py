# NG-COMPAT-TODO: retargeted at ch_cli_tools.ng.api.create_helm_chart/
# create_codefresh_deployment_scripts instead of the legacy ch_cli_tools.helm/
# ch_cli_tools.codefresh ones (ported from tests/test_codefresh.py). No
# preprocess_build_overrides() call - merging an overridden app/base-image's
# directory across layers happens transparently inside CHCodefresh.generate(),
# via CHContext.resolve_for_build(), the same mechanism create_skaffold_configuration
# already relies on.
#
# Scope of this file: the per-app/task/base-image/test-runner build steps
# (including their dependency/source-image build_arguments), the unit/api/e2e
# test steps, git-dependency clone steps, and the wait_deployment rollout-wait
# commands, all landing inside the template's pre-declared containers
# (steps.build_application_images.steps / steps.tests_unit.steps /
# steps.tests_api.scale / steps.tests_e2e.scale / steps.post_main_clone.steps /
# steps.wait_deployment.commands). Everything else legacy's
# create_codefresh_deployment_scripts also computes - parallel-step batching
# into build_application_images_N, stage ordering, secrets/db-connect-string/
# registry-secret wiring into the deployment step - is not generated yet, so
# none of that is asserted here.
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


def test_create_codefresh_configuration_rollout_wait_commands(tmp_path):
    # real cloud-harness samples app: harness.secured=true, subdomain=www,
    # harness.deployment.auto=true, harness.deployment.statefulset=true, no
    # explicit deployment.name (falls back to the app's own name).
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["samples"],
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

    commands = cf["steps"]["wait_deployment"]["commands"]

    # Template-provided context-setup commands survive untouched, first.
    assert commands[0] == "kubectl config use-context ${{CLUSTER_NAME}}"
    assert commands[1] == "kubectl config set-context --current --namespace=${{NAMESPACE}}"

    assert "kubectl rollout status statefulset/samples" in commands
    assert "kubectl rollout status deployment/www-gk" in commands

    # Gives the certificates time to settle, always last.
    assert commands[-1] == "sleep 60"


def test_create_codefresh_configuration_no_rollout_wait_commands_when_nothing_auto(
    tmp_path,
):
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

    commands = cf["steps"]["wait_deployment"]["commands"]
    # myapp has no deployment.auto/secured set - only the template's own
    # static context-setup commands remain, no rollout/sleep lines appended.
    assert commands == [
        "kubectl config use-context ${{CLUSTER_NAME}}",
        "kubectl config set-context --current --namespace=${{NAMESPACE}}",
    ]


def test_create_codefresh_configuration_gatekeeper_wait_suppressed_when_unsecured(
    tmp_path,
):
    # create_helm_chart's secured=False (-u/--disable-security on the CLI) turns
    # off gatekeeper rollout-waits project-wide, even for a secured app.
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["samples"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
        secured=False,
    )
    assert values["secured_gatekeepers"] is False

    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    commands = cf["steps"]["wait_deployment"]["commands"]
    assert "kubectl rollout status deployment/www-gk" not in commands
    # samples' own deployment.auto rollout-wait is unaffected - only the
    # gatekeeper wait is gated by secured_gatekeepers.
    assert "kubectl rollout status statefulset/samples" in commands


def test_create_codefresh_configuration_api_and_e2e_test_steps(tmp_path):
    # real cloud-harness samples app: subdomain=www, test.api/test.e2e both
    # enabled, a real api/openapi.yaml (servers: [{url: /api}]), and both a
    # test/api and test/e2e directory of its own custom tests.
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["samples"],
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

    api_steps = cf["steps"]["tests_api"]["scale"]
    api_step = api_steps["samples_api_test"]
    assert api_step["environment"] == ["APP_URL=https://www.${{DOMAIN}}/api"]
    assert len(api_step["volumes"]) == 2
    assert any("allvalues.yaml" in v for v in api_step["volumes"])
    assert len(api_step["commands"]) == 2
    st_cmd = api_step["commands"][0]
    assert "--pre-run cloudharness_test.apitest_init" in st_cmd
    assert "run api/openapi.yaml" in st_cmd
    assert "--base-url https://www.${{DOMAIN}}/api" in st_cmd
    assert "-c all" in st_cmd
    assert "--hypothesis-deadline=180000" in st_cmd
    assert api_step["commands"][1] == "pytest -v test/api"

    # test-api runner image gets a real build step, with its own dependency
    # build-args resolved the same way every other build step's are.
    build_steps = cf["steps"]["build_application_images"]["steps"]
    assert "CLOUDHARNESS_BASE" in " ".join(build_steps["test-api"]["build_arguments"])
    assert cf["steps"]["tests_api"]["image"] == build_steps["test-api"]["image_name"]

    e2e_steps = cf["steps"]["tests_e2e"]["scale"]
    e2e_step = e2e_steps["samples_e2e_test"]
    assert e2e_step["environment"] == ["APP_URL=https://www.${{DOMAIN}}"]
    assert len(e2e_step["volumes"]) == 1
    assert e2e_step["volumes"][0].endswith("applications/samples/test/e2e:/home/test/__tests__/samples")
    assert cf["steps"]["tests_e2e"]["image"] == build_steps["test-e2e"]["image_name"]


def test_create_codefresh_configuration_no_api_e2e_steps_when_not_enabled(tmp_path):
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

    # myapp has no test.api/test.e2e enabled - both steps get pruned entirely,
    # and no test-api/test-e2e runner image is built for nothing.
    assert "tests_api" not in cf["steps"]
    assert "tests_e2e" not in cf["steps"]
    assert "test-api" not in cf["steps"]["build_application_images"]["steps"]
    assert "test-e2e" not in cf["steps"]["build_application_images"]["steps"]
