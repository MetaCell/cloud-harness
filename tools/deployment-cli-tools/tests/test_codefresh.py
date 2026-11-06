# Merging an overridden app/base-image's directory across layers happens
# transparently inside CHCodefresh.generate(), via CHContext.resolve_for_build(),
# the same mechanism create_skaffold_configuration relies on - no separate
# preprocess_build_overrides() call is needed.
#
# Scope of this file: the per-app/task/base-image/test-runner build steps
# (including their dependency/source-image build_arguments, their own
# stage/registry/buildkit/NOCACHE fields from cloud-harness's own
# codefresh-build-template.yaml, their build-skip `when` condition, and never
# generating one for an app with an explicit harness.deployment.image), their
# sibling publish steps, parallel-step batching of build steps into
# build_application_images_N groups and top-level stage ordering, the
# unit/api/e2e test steps, git-dependency clone steps, the wait_deployment
# rollout-wait commands, the deployment step's secrets/db-connect-string/
# registry-secret custom_values, the prepare_deployment $PATHS/$ENV/$PARAMS
# substitution, and write_env_file, all landing inside the template's
# pre-declared containers (steps.build_application_images_N.steps /
# steps.publish.steps / steps.tests_unit.steps / steps.tests_api.scale /
# steps.tests_e2e.scale / steps.post_main_clone.steps /
# steps.wait_deployment.commands / steps.deployment.arguments.custom_values /
# steps.prepare_deployment.commands).
# That's the full feature set - nothing else is deliberately left out, with
# one exception: a per-app build.yaml override once read the file and
# discarded the result (`build_specific` was never merged anywhere) - dead
# code, untested anywhere; not implemented here, there's no working behavior
# to match.
import os
import shutil
import tempfile
from unittest.mock import patch

from conftest import CLOUDHARNESS_ROOT, RESOURCES
from test_util import write_tree_from_yaml

from ch_cli_tools.api import (
    create_codefresh_deployment_scripts,
    create_helm_chart,
    write_env_file,
)


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

    # The build step's own tag is the entity's pipeline-variable tag
    # reference (${{MYAPP_TAG}}), the same variable write_env_file exports
    # during prepare_deployment - not an unrelated built-in variable like
    # CF_SHORT_REVISION, so the image this step pushes is the exact one the
    # Helm chart's deployment.image already references.
    assert myapp_step["tag"] == "${{MYAPP_TAG}}"

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
    assert (
        base_step["dockerfile"] ==
        "infrastructure/base-images/cloudharness-base/Dockerfile"
    )
    assert "testprojectname/" in base_step["image_name"]

    # my-common: a common-image local to RESOURCES, never overridden - builds
    # straight from its own directory, dockerfile name alone (context == its own dir).
    common_step = steps["my-common"]
    assert common_step["dockerfile"] == "Dockerfile"
    assert common_step["working_directory"].endswith(
        "infrastructure/common-images/my-common"
    )

    # myapp's own task gets its own build step too, alongside the app.
    assert "myapp-mytask" in steps


def test_create_codefresh_configuration_app_without_build_dependency_still_builds(
    tmp_path,
):
    # Legacy regression: the apps directory was only scanned if task-images
    # was non-empty project-wide, so an app with a Dockerfile but no build
    # dependency on any task image (like accounts) could be silently skipped
    # entirely. Structurally impossible in ng - generate()'s app loop runs
    # unconditionally, never gated on task-images existing - but cheap to
    # keep as a basic invariant check.
    cf, _ = _generate_cf(tmp_path, ["accounts"])
    assert "accounts" in _build_steps(cf)


def test_create_codefresh_configuration_build_arguments(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    steps = _build_steps(cf)
    myapp_args = dict(arg.split("=", 1) for arg in steps["myapp"]["build_arguments"])

    # harness.dependencies.build (cloudharness-flask, plus my-common added by
    # values-dev.yaml) resolve to the dependency's own pipeline-variable tag
    # reference (the same one write_env_file exports during
    # prepare_deployment) - not a bare/unqualified name, and not an unrelated
    # built-in variable like CF_SHORT_REVISION. The registry prefix is the
    # literal ${{REGISTRY}} pipeline variable, not a resolved string: this
    # file is committed and only regenerated on env/config changes, never
    # when the REGISTRY variable itself is rotated in the Codefresh UI, so
    # baking in today's resolved value would silently go stale - matching
    # legacy's own image_tag_with_variables exactly.
    assert (
        myapp_args["CLOUDHARNESS_FLASK"] ==
        "${{REGISTRY}}/testprojectname/cloudharness-flask:${{CLOUDHARNESS_FLASK_TAG}}"
    )
    assert (
        myapp_args["MY_COMMON"] ==
        "${{REGISTRY}}/testprojectname/my-common:${{MY_COMMON_TAG}}"
    )

    # Globally ARG-pinned source images (from real cloud-harness base images'
    # own Dockerfiles) are merged in too - the same value on every build step,
    # even one (cloudharness-base) with no dependencies of its own.
    assert myapp_args["NODE"] == "node:22-alpine"
    base_args = dict(
        arg.split("=", 1) for arg in steps["cloudharness-base"]["build_arguments"]
    )
    assert base_args["NODE"] == myapp_args["NODE"]


def test_create_codefresh_configuration_source_images_override_wins_on_collision(
    tmp_path,
):
    # CLOUDHARNESS_FLASK is also a build dependency of myapp: a project-level
    # source_images override for it must win over the dependency-derived
    # build argument, not be shadowed by it.
    override_root = write_tree_from_yaml(
        tmp_path / "override",
        """
        deployment-configuration:
          values-template.yaml: |
            source_images:
              CLOUDHARNESS_FLASK: myoverride/cloudharness-flask:9.9
    """,
    )

    roots = [CLOUDHARNESS_ROOT, RESOURCES, override_root]
    values = create_helm_chart(
        roots,
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
        roots, envs=["dev"], helm_values=values, save=False
    )

    myapp_args = dict(
        arg.split("=", 1) for arg in _build_steps(cf)["myapp"]["build_arguments"]
    )
    assert myapp_args["CLOUDHARNESS_FLASK"] == "myoverride/cloudharness-flask:9.9"


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

    # Any other never-populated empty parallel container from the template
    # (build_test_images is never wired up by anything) is pruned the same way.
    assert "build_test_images" not in cf["steps"]


def test_parallel_build_steps_sorted_alphabetically(tmp_path):
    """Sub-steps inside every generated parallel step must be sorted alphabetically."""
    cf, _ = _generate_cf(tmp_path, ["samples", "myapp", "workflows"])

    for step_name, step in cf["steps"].items():
        if (
            step and
            isinstance(step, dict) and
            step.get("type") == "parallel" and
            "steps" in step
        ):
            sub_step_names = list(step["steps"].keys())
            assert sub_step_names == sorted(sub_step_names), (
                f"Sub-steps of '{step_name}' are not sorted alphabetically: {sub_step_names}"
            )


def test_steps_ordered_by_stage_in_generated_config(tmp_path):
    """The steps produced by create_codefresh_deployment_scripts must be ordered by stage."""
    cf, _ = _generate_cf(tmp_path, ["samples", "myapp", "workflows"])

    stages = cf.get("stages", [])
    stage_order = {s: i for i, s in enumerate(stages)}
    steps = cf["steps"]

    step_stage_indices = [
        stage_order.get(step.get("stage"), len(stages))
        for step in steps.values()
        if step and isinstance(step, dict)
    ]

    assert step_stage_indices == sorted(step_stage_indices), (
        "Steps are not ordered by stage. Got stages: " +
        str(
            [
                step.get("stage")
                for step in steps.values()
                if step and isinstance(step, dict)
            ]
        )
    )


def test_create_codefresh_configuration_publish_steps(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    publish_steps = cf["steps"]["publish"]["steps"]

    # Every buildable entity (app, base image, dependency) gets its own
    # publish step, re-pushing the exact image+tag this run just built.
    myapp_publish = publish_steps["publish_myapp"]
    assert myapp_publish["type"] == "push"
    assert myapp_publish["stage"] == "publish"
    # Same tag reference the build step itself used (${{MYAPP_TAG}}, exported
    # by write_env_file during prepare_deployment) - not an unrelated
    # built-in variable like CF_SHORT_REVISION, so publish re-pushes the
    # exact image the deployed Helm chart actually references. Registry is
    # the literal ${{REGISTRY}} pipeline variable, not a resolved string -
    # see CHCodefresh.qualify's own docstring for why.
    assert (
        myapp_publish["candidate"] ==
        "${{REGISTRY}}/testprojectname/myapp:${{MYAPP_TAG}}"
    )
    assert myapp_publish["tags"] == ["${{DEPLOYMENT_PUBLISH_TAG}}", "latest"]
    assert myapp_publish["registry"] == "${{REGISTRY_PUBLISH_URL}}"
    assert (
        "MYAPP_PUBLISH_SKIP" in myapp_publish["when"]["condition"]["all"]["skipPublish"]
    )

    assert "publish_cloudharness-flask" in publish_steps
    assert "publish_my-common" in publish_steps
    assert "publish_myapp-mytask" in publish_steps

    # Exact string match (not just substring) for a base image, not just an
    # app - confirms the same skipPublish condition mechanism applies
    # identically regardless of entity kind, matching legacy verbatim.
    base_publish = publish_steps["publish_cloudharness-base"]
    assert (
        base_publish["when"]["condition"]["all"]["skipPublish"] ==
        "includes('${{CLOUDHARNESS_BASE_PUBLISH_SKIP}}', "
        "'{{CLOUDHARNESS_BASE_PUBLISH_SKIP}}') == true"
    )


def test_create_codefresh_configuration_nested_task_working_directory(tmp_path):
    # workflows-notify-queue is a task nested two levels deep
    # (applications/workflows/tasks/notify-queue), not a single-level one
    # like myapp-mytask - its build step's context must still resolve to its
    # own real directory, not get confused by the extra nesting depth.
    cf, _ = _generate_cf(tmp_path, ["workflows"])

    build_steps = _build_steps(cf)
    step = build_steps["workflows-notify-queue"]
    assert step["dockerfile"] == "Dockerfile"
    assert step["working_directory"].endswith(
        "applications/workflows/tasks/notify-queue"
    )


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
    # Matches legacy's image_tag_with_variables exactly: the literal
    # ${{REGISTRY}} pipeline variable (not a resolved string - see
    # CHCodefresh.qualify's docstring) plus the entity's own tag reference.
    assert step["image"] == "${{REGISTRY}}/testprojectname/myapp:${{MYAPP_TAG}}"


def test_create_codefresh_configuration_no_unit_tests_when_not_included(tmp_path):
    """An app with no test.unit.commands gets no unit test step at all - and
    since nothing else populates tests_unit either, the whole now-empty
    parallel container is pruned, matching legacy's own "remove useless
    steps" filter."""
    cf, _ = _generate_cf(tmp_path, ["accounts"])

    assert "tests_unit" not in cf["steps"]


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
    assert (
        commands[1] == "kubectl config set-context --current --namespace=${{NAMESPACE}}"
    )

    assert "kubectl rollout status statefulset/samples" in commands
    assert "kubectl rollout status deployment/www-gk" in commands

    # Gives the certificates time to settle, always last.
    assert commands[-1] == "sleep 60"


def test_create_codefresh_configuration_rollout_wait_uses_plain_deployment_kind(
    tmp_path,
):
    # real cloud-harness accounts app: harness.deployment.auto=true, no
    # statefulset set - a plain, non-statefulset Deployment. `kubectl rollout
    # status deployment/x` fails outright when x is actually a StatefulSet,
    # so the two kinds must never be conflated in either direction.
    cf, _ = _generate_cf(tmp_path, ["accounts"])

    commands = cf["steps"]["wait_deployment"]["commands"]
    assert "kubectl rollout status deployment/accounts" in commands
    assert "kubectl rollout status statefulset/accounts" not in commands


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


def test_create_codefresh_configuration_deployment_secret_values(tmp_path):
    # real cloud-harness samples app: harness.secrets.asecret = "value" (a
    # simple-form, CloudHarness-managed secret). myapp: harness.database.
    # connect_string = "" (auto-generated, needs a pipeline-resolved value).
    cf, _ = _generate_cf(tmp_path, ["samples", "myapp"])

    custom_values = cf["steps"]["deployment"]["arguments"]["custom_values"]
    assert 'apps_samples_harness_secrets_asecret="${{ASECRET}}"' in custom_values
    assert (
        'apps_myapp_harness_database_connect__string="${{MYAPP_DB_CONNECT_STRING}}"'
        in custom_values
    )
    # No registry secret configured for this run.
    assert not any(v.startswith("registry_secret_value=") for v in custom_values)


def test_create_codefresh_configuration_registry_secret_value(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"], registry_secret_name="my-pull-secret")

    custom_values = cf["steps"]["deployment"]["arguments"]["custom_values"]
    assert 'registry_secret_value="${{K8S_SA_JSON}}"' in custom_values


def test_create_codefresh_configuration_secret_filtering(tmp_path):
    """Only secrets CloudHarness itself manages, with a real value still to be
    set, get exported as a deployment custom_values pipeline-variable
    reference - everything else (already-generated static values, secrets
    delegated to an external manager, explicitly unmanaged ones) is skipped.
    Adds a third, override-only layer on top of the real [CLOUDHARNESS_ROOT,
    RESOURCES] chain so myapp's real fixture values.yaml doesn't need to carry
    every exotic secret shape itself."""
    override_root = write_tree_from_yaml(
        tmp_path / "override",
        """
        applications:
          myapp:
            deploy:
              values.yaml: |
                harness:
                  secrets:
                    plain_secret: null
                    static_random: ""
                    rich_secret:
                      default: null
                    rich_static_random:
                      manager: cloudharness
                      default: ""
                    op_secret:
                      manager: onepassword
                      path: vaults/v/items/i
                    unmanaged_secret:
                      manager: null
    """,
    )

    roots = [CLOUDHARNESS_ROOT, RESOURCES, override_root]
    values = create_helm_chart(
        roots,
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
        roots, envs=["dev"], helm_values=values, save=False
    )

    custom_values = [
        v
        for v in cf["steps"]["deployment"]["arguments"]["custom_values"]
        if v.startswith("apps_myapp_harness_secrets_")
    ]
    assert custom_values == [
        'apps_myapp_harness_secrets_plain__secret="${{PLAIN__SECRET}}"',
        # the rich form nests the value under `default`
        'apps_myapp_harness_secrets_rich__secret_default="${{RICH__SECRET}}"',
    ]


def test_create_codefresh_configuration_secret_value_containing_quotes(tmp_path):
    # The secret's own value is never written into the generated YAML - only
    # a pipeline-variable reference is - so a value containing quotes must
    # produce exactly the same entry shape as any other secret, with no
    # escaping/quoting issue leaking through.
    override_root = write_tree_from_yaml(
        tmp_path / "override",
        """
        applications:
          myapp:
            deploy:
              values.yaml: |
                harness:
                  secrets:
                    settings_secret: "SECRET_KEY='replace-with-strong-shared-secret'"
    """,
    )

    roots = [CLOUDHARNESS_ROOT, RESOURCES, override_root]
    values = create_helm_chart(
        roots,
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
        roots, envs=["dev"], helm_values=values, save=False
    )

    custom_values = cf["steps"]["deployment"]["arguments"]["custom_values"]
    entry = next(
        v
        for v in custom_values
        if v.startswith("apps_myapp_harness_secrets_settings__secret=")
    )
    assert (
        entry == 'apps_myapp_harness_secrets_settings__secret="${{SETTINGS__SECRET}}"'
    )


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
    # The runner image's own tag reference is appended - same convention as
    # every other image reference embedded in codefresh.yaml.
    assert (
        cf["steps"]["tests_api"]["image"] ==
        build_steps["test-api"]["image_name"] + ":${{TEST_API_TAG}}"
    )

    e2e_steps = cf["steps"]["tests_e2e"]["scale"]
    e2e_step = e2e_steps["samples_e2e_test"]
    assert e2e_step["environment"] == ["APP_URL=https://www.${{DOMAIN}}"]
    assert len(e2e_step["volumes"]) == 1
    assert e2e_step["volumes"][0].endswith(
        "applications/samples/test/e2e:/home/test/__tests__/samples"
    )
    assert (
        cf["steps"]["tests_e2e"]["image"] ==
        build_steps["test-e2e"]["image_name"] + ":${{TEST_E2E_TAG}}"
    )


def test_create_codefresh_configuration_api_test_volumes_dont_leak_between_apps(
    tmp_path,
):
    # common's Dockerfile lives in a non-top-level subdirectory
    # (applications/common/server/Dockerfile) - its api test step's volumes
    # must still mount the app's own directory (applications/common), not
    # leak that "server" subdirectory into the path, and samples' volumes
    # must be unaffected by common being generated alongside it.
    cf, _ = _generate_cf(tmp_path, ["samples", "common"])

    api_steps = cf["steps"]["tests_api"]["scale"]
    common_step = api_steps["common_api_test"]
    for volume in common_step["volumes"]:
        assert "server" not in volume

    assert "samples_api_test" in api_steps


def test_create_codefresh_configuration_no_api_e2e_steps_when_not_enabled(tmp_path):
    cf, _ = _generate_cf(tmp_path, ["myapp"])

    # myapp has no test.api/test.e2e enabled - both steps get pruned entirely,
    # and no test-api/test-e2e runner image is built for nothing.
    assert "tests_api" not in cf["steps"]
    assert "tests_e2e" not in cf["steps"]
    build_steps = _build_steps(cf)
    assert "test-api" not in build_steps
    assert "test-e2e" not in build_steps


def test_create_codefresh_configuration_test_image_found_across_root_boundary(
    tmp_path,
):
    # Regression: the test-e2e runner image lives in CLOUDHARNESS_ROOT
    # (root_paths[0]), but the app that enables e2e testing (myapp) lives in
    # a higher-priority layer (RESOURCES, root_paths[1]) - it must still be
    # found and built, not missed because the two live in different layers.
    # An override-only third layer enables myapp's e2e tests without
    # permanently changing its real fixture values.yaml.
    override_root = write_tree_from_yaml(
        tmp_path / "override",
        """
        applications:
          myapp:
            deploy:
              values.yaml: |
                harness:
                  test:
                    e2e:
                      enabled: true
                      smoketest: false
    """,
    )

    roots = [CLOUDHARNESS_ROOT, RESOURCES, override_root]
    values = create_helm_chart(
        roots,
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
        roots, envs=["dev"], helm_values=values, save=False
    )

    assert "myapp_e2e_test" in cf["steps"]["tests_e2e"]["scale"]
    assert "test-e2e" in _build_steps(cf)


def test_create_codefresh_configuration_excluding_common_app_keeps_my_common_image(
    tmp_path,
):
    # Excluding the app named "common" must not skip the differently-scoped
    # "my-common" static/common image under infrastructure/common-images -
    # base/common images are a separate registry, never filtered by app
    # excludes.
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["common"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )
    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, RESOURCES], envs=["dev"], helm_values=values, save=False
    )

    assert "my-common" in _build_steps(cf)


def test_create_codefresh_configuration_no_build_for_app_with_prebuilt_image(tmp_path):
    # An app with harness.deployment.image set uses that pre-built image
    # instead of a locally-built one, even if it also has a Dockerfile
    # checked in - legacy's own `build` flag (ch_cli_tools/helm.py:374) is
    # `not bool(deployment_image)`, which ng already derives the same way via
    # CHApp.is_buildable. In legacy this same flag lives inside the
    # single per-Dockerfile loop that also generates git-clone/unit/api/e2e
    # steps, so a non-buildable app gets none of those either - only a
    # buildable app alongside it does.
    write_tree_from_yaml(
        tmp_path,
        """
        deployment-configuration:
          values-template.yaml: |
            name: testproj
            mainapp: appa
        applications:
          appa:
            Dockerfile: |
              FROM scratch
            deploy:
              values.yaml: |
                harness:
                  test:
                    unit:
                      enabled: true
                      commands: ['pytest tests/appa']
                    api:
                      enabled: false
                      autotest: false
                      checks: []
                    e2e:
                      enabled: false
                      smoketest: false
                  dependencies:
                    git:
                      - url: https://github.com/a/b.git
                        branch_tag: main
          appb:
            Dockerfile: |
              FROM scratch
            deploy:
              values.yaml: |
                harness:
                  deployment:
                    image: external/prebuilt:1.0
                  subdomain: appb
                  test:
                    unit:
                      enabled: true
                      commands: ['pytest tests/appb']
                    api:
                      enabled: true
                      autotest: false
                      checks: []
                    e2e:
                      enabled: true
                      smoketest: false
                  dependencies:
                    git:
                      - url: https://github.com/x/y.git
                        branch_tag: main
            api:
              openapi.yaml: |
                servers:
                  - url: /api
    """,
    )

    values = create_helm_chart(
        [tmp_path],
        output_path=tmp_path,
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )
    cf = create_codefresh_deployment_scripts(
        [tmp_path], envs=["dev"], helm_values=values, save=False
    )

    build_steps = _build_steps(cf)
    assert "appa" in build_steps
    assert "appb" not in build_steps
    publish_steps = cf["steps"]["publish"]["steps"]
    assert "publish_appa" in publish_steps
    assert "publish_appb" not in publish_steps

    unit_steps = cf["steps"]["tests_unit"]["steps"]
    assert "appa_ut" in unit_steps
    assert "appb_ut" not in unit_steps

    clone_steps = cf["steps"]["post_main_clone"]["steps"]
    assert any("appa" in name for name in clone_steps)
    assert not any("appb" in name for name in clone_steps)

    # appb is the only app with api/e2e enabled - gated off entirely, so
    # both containers end up empty and are pruned, same as "not included".
    assert "tests_api" not in cf["steps"]
    assert "tests_e2e" not in cf["steps"]


def test_create_codefresh_configuration_nobuild(tmp_path):
    # myapp's nobuild env sets harness.deployment.image (not buildable) and
    # clears dependencies.build (there's no resolvable cloud-harness-provided
    # dependency in this single-root [RESOURCES] chain) - myapp itself gets no
    # build/publish step, but its own task - independent of the owning app's
    # buildability - still does. (Legacy also asserts the generated build
    # group contains *only* the task image - not reproduced here: legacy's
    # own scan gates base/common-image discovery behind whether any
    # task-images exist at all, so cloudharness-base/my-common happen to be
    # filtered out in that specific scenario; ng's base_images registry
    # always includes them regardless, a deliberate, already-tested
    # difference, not a regression.)
    values = create_helm_chart(
        [RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env=["dev", "nobuild"],
        local=False,
        tag="1",
        registry="reg",
    )
    cf = create_codefresh_deployment_scripts(
        [RESOURCES], envs=["dev", "nobuild"], helm_values=values, save=False
    )

    build_steps = _build_steps(cf)
    assert "myapp-mytask" in build_steps
    assert "myapp" not in build_steps

    assert "publish_myapp" not in cf["steps"]["publish"]["steps"]
    assert "publish_myapp-mytask" in cf["steps"]["publish"]["steps"]


def test_create_codefresh_deployment_scripts_save_writes_under_deployment_dir(tmp_path):
    # save=True (the real CLI's default) must write next to where helm's own
    # chart lands - root/deployment/codefresh-{env}.yaml - not CWD/codefresh-
    # {env}.yaml. Regression test for a bug where generate()'s own
    # output_path="." default didn't match CHCodefresh.path's actual location.
    # Uses its own synthetic single-root project, not the shared
    # [CLOUDHARNESS_ROOT, RESOURCES] fixture _generate_cf relies on.
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


def test_create_codefresh_configuration_paths_are_cwd_independent(tmp_path):
    # $PATHS and build steps' working_directory must not depend on the
    # process's current working directory - ng resolves every path via
    # Path.resolve() rather than legacy's os.path.relpath(path, '.'), so
    # running from an unrelated sibling directory must produce identical
    # results: no "../cloud-harness" leaking through, and no build step
    # working_directory that escapes via ".." or turns up absolute.
    sibling_dir = tempfile.mkdtemp(dir=str(CLOUDHARNESS_ROOT.parent))
    old_cwd = os.getcwd()
    try:
        os.chdir(sibling_dir)
        cf, _ = _generate_cf(tmp_path, ["samples"])
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(sibling_dir, ignore_errors=True)

    deploy_cmd = next(
        c
        for c in cf["steps"]["prepare_deployment"]["commands"]
        if "harness-deployment" in c
    )
    assert "../cloud-harness" not in deploy_cmd

    build_steps = _build_steps(cf)
    ch_steps = {
        name: step
        for name, step in build_steps.items()
        if "cloudharness" in name or name == "samples"
    }
    assert ch_steps, "expected at least one cloud-harness image build step"
    for name, step in ch_steps.items():
        wd = step.get("working_directory", "")
        assert not wd.startswith("../") and "/../" not in wd, (
            f"'{name}' working_directory escapes via '..': {wd}"
        )
        assert not os.path.isabs(wd), f"'{name}' working_directory is absolute: {wd}"


def test_create_codefresh_configuration_top_level_app_working_directory(tmp_path):
    """An app declared directly under the TOP project's own root (not a
    RESOURCES-nested fixture, and not overridden from a lower layer) must get
    a plain, project-root-relative working_directory. Using deployment/
    instead of the project root as the relativization base silently prepends
    a spurious '../' here - the regression a real multi-root deployment hit,
    since every fixture elsewhere in this file lives outside the project
    root it's layered under and so never exercises this path."""
    top_root = tmp_path / "top"
    write_tree_from_yaml(
        top_root,
        """
        applications:
          ownapp:
            Dockerfile: |
              FROM scratch
            deploy:
              values.yaml: |
                harness:
                  subdomain: ownapp
                  deployment:
                    auto: true
        """,
    )
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, top_root],
        output_path=tmp_path / "out",
        include=["ownapp"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )
    cf = create_codefresh_deployment_scripts(
        [CLOUDHARNESS_ROOT, top_root],
        envs=["dev"],
        helm_values=values,
        save=False,
    )

    step = _build_steps(cf)["ownapp"]
    assert step["working_directory"] == "applications/ownapp"
    assert step["dockerfile"] == "Dockerfile"


def test_create_codefresh_configuration_multienv(tmp_path):
    # Multiple envs merge in order - later envs win on a shared key, each
    # env's own keys are additive. RESOURCES' own codefresh-template-{dev,test}
    # fixtures each set a distinct top-level scalar flag; CLOUDHARNESS_ROOT's
    # real codefresh-template-test.yaml is a full alternate pipeline (its own
    # namespace naming, no publish step) - test must win on prepare_deployment
    # since it's merged in after dev.
    include = ["samples", "myapp", "workflows"]
    roots = [CLOUDHARNESS_ROOT, RESOURCES]
    values = create_helm_chart(
        roots,
        output_path=tmp_path,
        include=include,
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env=["dev", "test"],
        local=False,
        tag="1",
        registry="reg",
    )
    cf = create_codefresh_deployment_scripts(
        roots, envs=["dev", "test"], helm_values=values, save=False
    )

    assert cf["test_step"] == "test"
    assert cf["test"] is True
    assert cf["dev"] is True

    commands = cf["steps"]["prepare_deployment"]["commands"]
    harness_deployment_cmds = [c for c in commands if "harness-deployment" in c]
    assert harness_deployment_cmds
    for cmd in harness_deployment_cmds:
        assert "-e dev-test" in cmd
        assert "test-${{NAMESPACE_BASENAME}}" in cmd
        for inc in include:
            assert f"-i {inc}" in cmd


def test_write_env_file(tmp_path):
    _, values = _generate_cf(tmp_path, ["myapp"])

    env_file = tmp_path / "test.env"
    with patch(
        "ch_cli_tools.ci.check_image_exists_in_registry",
        side_effect=[True, False, True, False, True, False, True, False],
    ) as mock_check:
        write_env_file(values, str(env_file))

    lines = env_file.read_text().splitlines()
    env = dict(line.split("=", 1) for line in lines)

    # myapp itself, its instance (running the same image), its own task, a
    # declared build dependency (cloudharness-flask, via task-images), and the
    # test-api/test-e2e runner images (read straight from the model, never
    # part of helm_values itself) all get a tag line.
    assert env["MYAPP_TAG"] == "1"
    assert env["MYAPP_INST1_TAG"] == "1"
    assert env["MYAPP_MYTASK_TAG"] == "1"
    assert env["CLOUDHARNESS_FLASK_TAG"] == "1"
    assert env["TEST_API_TAG"] == "1"
    assert env["TEST_E2E_TAG"] == "1"

    # Registry-existence check drives the _EXISTS/_NEW suffix, one call per
    # recorded image - alternating True/False above must split the same way.
    assert mock_check.call_count == 8
    exists_suffixes = [k for k in env if k.endswith("_EXISTS")]
    new_suffixes = [k for k in env if k.endswith("_NEW")]
    assert len(exists_suffixes) == 4
    assert len(new_suffixes) == 4
