# NG-COMPAT-TODO: retargeted at ch_cli_tools.ng.api.create_helm_chart/
# create_codefresh_deployment_scripts instead of the legacy ch_cli_tools.helm/
# ch_cli_tools.codefresh ones (ported from tests/test_codefresh.py). No
# preprocess_build_overrides() call - merging an overridden app/base-image's
# directory across layers happens transparently inside CHCodefresh.generate(),
# via CHContext.resolve_for_build(), the same mechanism create_skaffold_configuration
# already relies on.
#
# Scope of this file: the per-app/task/base-image/test-runner build steps
# (including their dependency/source-image build_arguments, their own
# stage/registry/buildkit/NOCACHE fields from cloud-harness's own
# codefresh-build-template.yaml, and their build-skip `when` condition), their
# sibling publish steps, parallel-step batching of build steps into
# build_application_images_N groups and top-level stage ordering, the
# unit/api/e2e test steps, git-dependency clone steps, the wait_deployment
# rollout-wait commands, the prepare_deployment $PATHS/$ENV/$PARAMS
# substitution, and write_env_file, all landing inside the template's
# pre-declared containers (steps.build_application_images_N.steps /
# steps.publish.steps / steps.tests_unit.steps / steps.tests_api.scale /
# steps.tests_e2e.scale / steps.post_main_clone.steps /
# steps.wait_deployment.commands / steps.prepare_deployment.commands).
# Everything else legacy's create_codefresh_deployment_scripts also computes -
# secrets/db-connect-string/registry-secret wiring into the deployment step -
# is not generated yet, so none of that is asserted here.
from unittest.mock import patch

from ch_cli_tools.ng.api import (
    create_helm_chart,
    create_codefresh_deployment_scripts,
    write_env_file,
)
from conftest import CLOUDHARNESS_ROOT, RESOURCES


def _build_steps(cf):
    """Merge every build_application_images_N group's steps into one dict -
    batching splits them by dependency order, most tests here don't care
    which group a given step landed in."""
    merged = {}
    for name, step in cf["steps"].items():
        if name.startswith("build_application_images"):
            merged.update(step.get("steps") or {})
    return merged


def _generate_cf(tmp_path, include, **helm_chart_kwargs):
    """create_helm_chart + create_codefresh_deployment_scripts against the real
    [CLOUDHARNESS_ROOT, RESOURCES] chain, with the fixed args every test in this
    file shares. Returns (codefresh_dict, helm_values) - most tests only need
    the former, a couple (e.g. secured_gatekeepers) need the latter too."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=include,
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
        **helm_chart_kwargs,
    )
    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES],
        envs=["dev"],
        helm_values=values,
        save=False,
    )
    return cf, values


def test_create_codefresh_configuration_build_steps(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["samples", "myapp"])

    # Template scaffolding (stages, main_clone, deployment, ...) survives untouched.
    assert cf["steps"]["main_clone"]["type"] == "git-clone"

    steps = _build_steps(cf)

    # myapp: own Dockerfile, env-specific dev.Dockerfile preferred, project name
    # ("testprojectname") overriding the image path.
    myapp_step = steps["myapp"]
    assert myapp_step["dockerfile"] == "dev.Dockerfile"
    assert "testprojectname/" in myapp_step["image_name"]

    # Every build step carries cloud-harness's own build-template defaults:
    # its own stage, the Codefresh registry reference, buildkit, and a
    # cache-busting NOCACHE build arg ahead of any dependency/source arg.
    assert myapp_step["stage"] == "build"
    assert myapp_step["registry"] == "${{CODEFRESH_REGISTRY}}"
    assert myapp_step["buildkit"] is True
    assert myapp_step["build_arguments"][0] == "NOCACHE=${{CF_BUILD_ID}}"

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
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    steps = _build_steps(cf)
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


def test_create_codefresh_configuration_build_skip_when_condition(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    steps = _build_steps(cf)
    when = steps["myapp"]["when"]["condition"]["any"]

    # Skip rebuilding if write_env_file's own MYAPP_TAG_EXISTS variable says
    # the registry already has this tag, unless MYAPP_TAG_FORCE_BUILD is set.
    assert "MYAPP_TAG_EXISTS" in when["buildDoesNotExist"]
    assert "MYAPP_TAG_FORCE_BUILD" in when["forceNoCache"]

    # Each entity gets its own, name-specific pair of variables.
    base_when = steps["cloudharness-base"]["when"]["condition"]["any"]
    assert "CLOUDHARNESS_BASE_TAG_EXISTS" in base_when["buildDoesNotExist"]


def test_create_codefresh_configuration_build_step_batching(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    group_names = sorted(
        (k for k in cf["steps"] if k.startswith("build_application_images_")),
        key=lambda k: int(k.rsplit("_", 1)[-1]),
    )
    groups = [cf["steps"][name] for name in group_names]
    assert groups, "expected at least one numbered build group"

    def group_of(name):
        return next(i for i, g in enumerate(groups) if name in g["steps"])

    # myapp depends on cloudharness-flask and my-common (harness.dependencies.
    # build) - both must be built in a strictly earlier parallel group.
    assert group_of("myapp") > group_of("cloudharness-flask")
    assert group_of("myapp") > group_of("my-common")

    # Each step carries no leftover internal "dependencies" bookkeeping field.
    assert "dependencies" not in groups[group_of("myapp")]["steps"]["myapp"]

    # Groups are numbered contiguously from 0, inherit the template's own
    # fields (stage), and get their own title.
    for i, group in enumerate(groups):
        assert group["title"] == f"Build parallel step {i + 1}"
        assert group["stage"] == "build"

    # The un-split container and unused placeholder slots don't leak through.
    assert "build_application_images" not in cf["steps"]
    assert "build_application_images_5" not in cf["steps"]


def test_create_codefresh_configuration_publish_steps(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    publish_steps = cf["steps"]["publish"]["steps"]

    # Every buildable entity (app, base image, dependency) gets its own
    # publish step, re-pushing the exact image+tag this run just built.
    myapp_publish = publish_steps["publish_myapp"]
    assert myapp_publish["type"] == "push"
    assert myapp_publish["stage"] == "publish"
    assert myapp_publish["candidate"] == "reg/testprojectname/myapp:${{CF_SHORT_REVISION}}"
    assert myapp_publish["tags"] == ["${{DEPLOYMENT_PUBLISH_TAG}}", "latest"]
    assert myapp_publish["registry"] == "${{REGISTRY_PUBLISH_URL}}"
    assert (
        "MYAPP_PUBLISH_SKIP" in myapp_publish["when"]["condition"]["all"]["skipPublish"]
    )

    assert "publish_cloudharness-flask" in publish_steps
    assert "publish_my-common" in publish_steps
    assert "publish_myapp-mytask" in publish_steps


def test_create_codefresh_configuration_no_publish_step_for_test_images(tmp_path):
    # real cloud-harness samples app pulls in the test-api/test-e2e runner
    # images - legacy never publishes those (publish=False), and neither
    # should ng.
    cf, _ = _generate_cf(tmp_path, ["samples"])

    publish_steps = cf["steps"]["publish"]["steps"]
    assert "publish_test-api" not in publish_steps
    assert "publish_test-e2e" not in publish_steps


def test_create_codefresh_configuration_unit_tests(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

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
    cf, _ = _generate_cf(tmp_path, ["accounts"])

    unit_steps = cf["steps"]["tests_unit"]["steps"]
    assert "accounts_ut" not in unit_steps


def test_create_codefresh_configuration_git_clone_steps(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

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
    cf, _ = _generate_cf(tmp_path, ["accounts"])

    clone_steps = cf["steps"]["post_main_clone"]["steps"]
    # Only the static template step is present - accounts has no git dependencies.
    assert list(clone_steps.keys()) == ["clone_cloud_harness"]


def test_create_codefresh_configuration_rollout_wait_commands(tmp_path):
    # real cloud-harness samples app: harness.secured=true, subdomain=www,
    # harness.deployment.auto=true, harness.deployment.statefulset=true, no
    # explicit deployment.name (falls back to the app's own name).
    cf, _ = _generate_cf(tmp_path, ["samples"])

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
    cf, _ = _generate_cf(tmp_path, ["myapp"])

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
    cf, values = _generate_cf(tmp_path, ["samples"], secured=False)
    assert values["secured_gatekeepers"] is False

    commands = cf["steps"]["wait_deployment"]["commands"]
    assert "kubectl rollout status deployment/www-gk" not in commands
    # samples' own deployment.auto rollout-wait is unaffected - only the
    # gatekeeper wait is gated by secured_gatekeepers.
    assert "kubectl rollout status statefulset/samples" in commands


def test_create_codefresh_configuration_api_and_e2e_test_steps(tmp_path):
    # real cloud-harness samples app: subdomain=www, test.api/test.e2e both
    # enabled, a real api/openapi.yaml (servers: [{url: /api}]), and both a
    # test/api and test/e2e directory of its own custom tests.
    cf, _ = _generate_cf(tmp_path, ["samples"])

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
    build_steps = _build_steps(cf)
    assert "CLOUDHARNESS_BASE" in " ".join(build_steps["test-api"]["build_arguments"])
    assert cf["steps"]["tests_api"]["image"] == build_steps["test-api"]["image_name"]

    e2e_steps = cf["steps"]["tests_e2e"]["scale"]
    e2e_step = e2e_steps["samples_e2e_test"]
    assert e2e_step["environment"] == ["APP_URL=https://www.${{DOMAIN}}"]
    assert len(e2e_step["volumes"]) == 1
    assert e2e_step["volumes"][0].endswith("applications/samples/test/e2e:/home/test/__tests__/samples")
    assert cf["steps"]["tests_e2e"]["image"] == build_steps["test-e2e"]["image_name"]


def test_create_codefresh_configuration_no_api_e2e_steps_when_not_enabled(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    # myapp has no test.api/test.e2e enabled - both steps get pruned entirely,
    # and no test-api/test-e2e runner image is built for nothing.
    assert "tests_api" not in cf["steps"]
    assert "tests_e2e" not in cf["steps"]
    build_steps = _build_steps(cf)
    assert "test-api" not in build_steps
    assert "test-e2e" not in build_steps


def test_create_codefresh_deployment_scripts_save_writes_under_deployment_dir(tmp_path):
    # save=True (the real CLI's default) must write next to where helm's own
    # chart lands - root/deployment/codefresh-{env}.yaml - not CWD/codefresh-
    # {env}.yaml. Regression test for a bug where generate()'s own
    # output_path="." default didn't match CHCodefresh.path's actual location.
    # Uses its own synthetic single-root project, not the shared
    # [CLOUDHARNESS_ROOT, RESOURCES] fixture _generate_cf relies on.
    (tmp_path / "deployment-configuration").mkdir(parents=True)
    (tmp_path / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\nmainapp: myapp\n"
    )
    app_dir = tmp_path / "applications" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")

    values = create_helm_chart(
        [tmp_path],
        output_path=tmp_path / "deployment",
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    create_codefresh_deployment_scripts(
        [tmp_path],
        envs=["dev"],
        helm_values=values,
        save=True,
    )

    assert (tmp_path / "deployment" / "codefresh-dev.yaml").exists()


def test_create_codefresh_configuration_prepare_deployment_placeholders(tmp_path):
    # include/exclude flow into $PARAMS via helm_values._ch_project.config,
    # inherited by create_codefresh_deployment_scripts automatically - no need
    # to pass them again here.
    cf, _ = _generate_cf(tmp_path, ["samples", "myapp"])

    deploy_cmd = next(
        c
        for c in cf["steps"]["prepare_deployment"]["commands"]
        if "harness-deployment" in c
    )
    # CLOUDHARNESS_ROOT is itself the cloud-harness checkout - rewritten to the
    # literal "cloud-harness" Codefresh clones it to, regardless of its real
    # local path; RESOURCES (the top of the chain) is "." relative to itself.
    assert "harness-deployment cloud-harness . -d" in deploy_cmd
    assert "-e dev " in deploy_cmd
    assert "-i samples -i myapp -ex events" in deploy_cmd
    assert "$PATHS" not in deploy_cmd
    assert "$ENV" not in deploy_cmd
    assert "$PARAMS" not in deploy_cmd


def test_write_env_file(tmp_path):
    _, values = _generate_cf(tmp_path, ["myapp"])

    env_file = tmp_path / "test.env"
    with patch(
        "ch_cli_tools.ng.codefresh.check_image_exists_in_registry",
        side_effect=[True, False, True, False, True, False, True],
    ) as mock_check:
        write_env_file(values, str(env_file))

    lines = env_file.read_text().splitlines()
    env = dict(line.split("=", 1) for line in lines)

    # myapp itself, its own task, a declared build dependency
    # (cloudharness-flask, via task-images), and the test-api/test-e2e runner
    # images (read straight from the model, never part of helm_values itself)
    # all get a tag line.
    assert env["MYAPP_TAG"] == "1"
    assert env["MYAPP_MYTASK_TAG"] == "1"
    assert env["CLOUDHARNESS_FLASK_TAG"] == "1"
    assert env["TEST_API_TAG"] == "1"
    assert env["TEST_E2E_TAG"] == "1"

    # Registry-existence check drives the _EXISTS/_NEW suffix, one call per
    # recorded image - alternating True/False above must split the same way.
    assert mock_check.call_count == 7
    exists_suffixes = [k for k in env if k.endswith("_EXISTS")]
    new_suffixes = [k for k in env if k.endswith("_NEW")]
    assert len(exists_suffixes) == 4
    assert len(new_suffixes) == 3
