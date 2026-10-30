"""End-to-end tests of the GitHub Actions workflow generator, over the same
[CLOUDHARNESS_ROOT, RESOURCES] chain and arguments test_codefresh.py uses."""

import os
import re
import shutil
import tempfile

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain
from ruamel.yaml import YAML
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig
from ch_cli_tools.api import create_helm_chart
from ch_cli_tools.github_actions import DEFAULT_RUNNER

JOB_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _generate(tmp_path, include, envs=("dev",), **helm_chart_kwargs):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path / "deployment",
        include=include,
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env=list(envs),
        local=False,
        tag="1",
        registry="reg",
        **helm_chart_kwargs,
    )
    project = values._ch_project
    return project.github_actions.generate(write_on_disk=False), project


def _step(job, step_id):
    return next(step for step in job["steps"] if step.get("id") == step_id)


def _steps(job, name_prefix):
    return [step for step in job["steps"] if str(step.get("name", "")).startswith(name_prefix)]


def _run_strings(workflow):
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if "run" in step:
                yield step["run"]


def test_template_layering(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])

    # cloud-harness base + env template, then the project's own dev overlay
    assert wf["name"] == "CloudHarness dev"
    assert wf["on"]["push"]["branches"] == ["develop"]
    assert "workflow_dispatch" in wf["on"]
    assert wf["permissions"]["packages"] == "write"
    assert wf["test_step"] == "dev"
    assert wf["jobs"]["prepare"]["name"] == "Overridden"
    # a job the project adds gets the dependency guard like any other
    custom = wf["jobs"]["custom-job"]
    assert custom["needs"] == ["deploy"]
    assert "needs.deploy.result == 'success'" in custom["if"]
    # an overlay for an expanded job id is merged over the generated job
    assert wf["jobs"]["build-myapp"]["runs-on"] == "big-runner"
    # the generator-only section is consumed, not emitted; its kube_auth steps replace
    # the default ones wherever a job asks for $KUBE_AUTH
    assert "cloudharness" not in wf
    for name in ("deploy", "wait-deployment"):
        steps = wf["jobs"][name]["steps"]
        assert [s for s in steps if s.get("name") == "Custom cluster access"], name
        assert not [s for s in steps if s.get("name") == "Configure kubectl"], name
    assert wf["jobs"]["deploy"]["environment"] == "dev"
    # only deploy is gated by the environment's protection rules, not every job using the cluster
    assert "environment" not in wf["jobs"]["wait-deployment"]
    # OIDC tokens are not minted for every job
    assert "id-token" not in wf["permissions"]


def test_build_jobs_follow_the_dependency_graph(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]

    for name in ("cloudharness-base", "cloudharness-flask", "myapp", "myapp-mytask", "my-common", "samples"):
        assert f"build-{name}" in jobs, name
    # only what the deployment needs is built: no excluded app, no unused base image
    assert "build-events" not in jobs
    assert "build-cloudharness-base-debian" not in jobs

    assert jobs["build-cloudharness-base"]["needs"] == ["prepare"]
    assert jobs["build-myapp"]["needs"][:2] == ["prepare", "build-cloudharness-flask"]
    assert jobs["build-cloudharness-flask"]["needs"] == ["prepare", "build-cloudharness-base"]

    condition = jobs["build-myapp"]["if"]
    assert "needs.prepare.outputs.MYAPP_TAG_EXISTS != '1'" in condition
    assert "!cancelled()" in condition
    assert "needs.prepare.result == 'success'" in condition
    # a skipped dependency build must not skip the dependant
    assert "needs.build-cloudharness-flask.result ==" not in condition


def test_build_step_inputs(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]

    build = _step(jobs["build-myapp"], "build")
    with_ = build["with"]
    assert with_["context"] == "./applications/myapp"
    assert with_["file"] == "./applications/myapp/dev.Dockerfile", "env Dockerfile preferred"
    assert isinstance(with_["build-args"], str) and isinstance(with_["tags"], str)
    build_args = with_["build-args"].splitlines()
    assert build_args[0] == "NOCACHE=${{ github.run_id }}"
    assert (
        "CLOUDHARNESS_FLASK=${{ vars.REGISTRY }}/testprojectname/cloudharness-flask:"
        "${{ needs.prepare.outputs.CLOUDHARNESS_FLASK_TAG }}" in build_args
    )
    tags = with_["tags"].splitlines()
    assert tags[0] == "${{ vars.REGISTRY }}/testprojectname/myapp:${{ needs.prepare.outputs.MYAPP_TAG }}"
    assert tags[1].endswith(":${{ needs.prepare.outputs.branch_tag }}")
    assert with_["push"] is True
    assert with_["cache-from"] == "type=registry,ref=${{ vars.REGISTRY }}/testprojectname/myapp:buildcache"
    assert "steps.check.outputs.exists != 'true'" in build["if"]
    assert "',myapp,'" in build["if"]

    check = _step(jobs["build-myapp"], "check")
    assert check["env"]["IMAGE"] == (
        "${{ vars.REGISTRY }}/testprojectname/myapp:${{ needs.prepare.outputs.MYAPP_TAG }}"
    )
    assert 'imagetools inspect "$IMAGE"' in check["run"]

    # cloudharness-base is overridden by RESOURCES: built from the merged .overrides context
    base = _step(jobs["build-cloudharness-base"], "build")["with"]
    assert base["context"] == "./.overrides/cloudharness-base"
    assert base["file"] == (
        "./.overrides/cloudharness-base/infrastructure/base-images/cloudharness-base/Dockerfile"
    )
    # samples lives in cloud-harness, cloned into ./cloud-harness by the workflow
    samples = _step(jobs["build-samples"], "build")["with"]
    assert samples["context"] == "./cloud-harness/applications/samples"
    assert samples["file"] == "./cloud-harness/applications/samples/Dockerfile"
    # a test image gets the extra latest tag
    assert "${{ vars.REGISTRY }}/testprojectname/test-e2e:latest" in (
        _step(jobs["build-test-e2e"], "build")["with"]["tags"].splitlines()
    )


def test_git_dependency_checkouts(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]

    clones = _steps(jobs["build-myapp"], "Clone ")
    clones = [step for step in clones if step["name"] != "Clone cloud-harness"]
    assert len(clones) == 2, "myapp declares two git dependencies"
    assert clones[0]["uses"] == "actions/checkout@v4"
    assert clones[0]["with"]["repository"] == "a/b"
    assert clones[0]["with"]["ref"] == "master"
    assert clones[0]["with"]["path"] == "applications/myapp/dependencies/b"
    step_names = [step.get("name") for step in jobs["build-myapp"]["steps"]]
    assert step_names.index("Clone b") < step_names.index("Build and push myapp")
    # prepare clones them too (the content hash needs them); samples has none
    assert len([s for s in _steps(jobs["prepare"], "Clone ") if s["name"] != "Clone cloud-harness"]) == 2
    assert not [s for s in _steps(jobs["build-samples"], "Clone ") if s["name"] != "Clone cloud-harness"]


def test_prepare_outputs_cover_every_build(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    outputs = wf["jobs"]["prepare"]["outputs"]

    assert list(outputs)[0] == "branch_tag", "template outputs come first"
    for job_name in wf["jobs"]:
        if not job_name.startswith("build-"):
            continue
        variable = job_name[len("build-"):].replace("-", "_").upper() + "_TAG"
        assert outputs[variable] == "${{ steps.images.outputs.%s }}" % variable
        assert outputs[f"{variable}_EXISTS"] == "${{ steps.images.outputs.%s_EXISTS }}" % variable
    # instances share their parent's image but still get their variables
    assert "MYAPP_INST1_TAG" in outputs


def test_unit_test_jobs(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]

    unit_jobs = [name for name in jobs if name.startswith("tests-unit-")]
    assert sorted(unit_jobs) == ["tests-unit-myapp", "tests-unit-samples"]
    job = jobs["tests-unit-myapp"]
    assert job["needs"] == ["prepare", "build-myapp"]
    assert "needs.prepare.result == 'success'" in job["if"]
    step = _steps(job, "Run myapp unit tests")[0]
    assert step["env"]["CH_TEST_IMAGE"] == (
        "${{ vars.REGISTRY }}/testprojectname/myapp:${{ needs.prepare.outputs.MYAPP_TAG }}"
    )
    assert step["env"]["CH_TEST_COMMANDS"].startswith("set -e\ntox\n")
    assert step["run"].startswith("docker run --rm")
    assert '"$CH_TEST_IMAGE" sh -c "$CH_TEST_COMMANDS"' in step["run"]
    # deploy waits for the unit tests, as the Codefresh unittest stage precedes deploy
    assert "tests-unit-myapp" in jobs["deploy"]["needs"]


def test_api_and_e2e_test_jobs(tmp_path):
    wf, _ = _generate(tmp_path, ["samples"])
    jobs = wf["jobs"]

    api = jobs["tests-api-samples"]
    assert "wait-deployment" in api["needs"] and "build-test-api" in api["needs"]
    assert "needs.prepare.outputs.skip_tests != 'true'" in api["if"]
    # wait-deployment may be skipped (it has its own `if`), but must not have failed
    assert "needs.wait-deployment.result ==" not in api["if"]
    assert "!contains(needs.*.result, 'failure')" in api["if"]
    step = _steps(api, "Run samples API tests")[0]
    assert step["env"]["APP_URL"] == "https://www.${{ vars.DOMAIN }}/api"
    assert step["env"]["CH_TEST_IMAGE"] == (
        "${{ vars.REGISTRY }}/testprojectname/test-api:${{ needs.prepare.outputs.TEST_API_TAG }}"
    )
    assert "-e APP_URL" in step["run"]
    assert '-v "$GITHUB_WORKSPACE/cloud-harness/applications/samples:/home/test"' in step["run"]
    assert "/opt/cloudharness/resources/allvalues.yaml" in step["run"]
    assert "-w /home/test" in step["run"]
    commands = step["env"]["CH_TEST_COMMANDS"].splitlines()
    assert "--pre-run cloudharness_test.apitest_init" in commands[1]
    assert "--base-url https://www.${{ vars.DOMAIN }}/api" in commands[1]
    assert commands[2] == "pytest -v test/api"

    e2e = jobs["tests-e2e-samples"]
    assert "build-test-e2e" in e2e["needs"]
    step = _steps(e2e, "Run samples E2E tests")[0]
    assert step["env"]["APP_URL"] == "https://www.${{ vars.DOMAIN }}"
    assert (
        '-v "$GITHUB_WORKSPACE/cloud-harness/applications/samples/test/e2e:/home/test/__tests__/samples"'
        in step["run"]
    )
    assert step["env"]["CH_TEST_COMMANDS"] == "set -e\nnpx puppeteer browsers install chrome\nyarn test\n"
    assert "commands" not in e2e, "the prototype's commands key never reaches the workflow"

    # the test runner images are built with the build prototype
    assert jobs["build-test-api"]["needs"] == ["prepare", "build-cloudharness-base"]
    assert "build-test-api" not in jobs["deploy"]["needs"]


def test_no_api_e2e_jobs_when_not_enabled(tmp_path):
    wf, _ = _generate(tmp_path, ["myapp"])
    names = list(wf["jobs"])
    assert not [n for n in names if n.startswith(("tests-api", "tests-e2e", "build-test-"))]
    assert "wait-deployment" in names
    # nothing references the removed prototypes any more
    for job in wf["jobs"].values():
        for need in job.get("needs", []):
            assert need in wf["jobs"], need


def test_deploy_secret_values(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], registry_secret_name="my-pull-secret")
    deploy = wf["jobs"]["deploy"]

    step = _steps(deploy, "Collect secret values")[0]
    assert step["env"]["ASECRET"] == "${{ secrets.ASECRET }}"
    assert step["env"]["MYAPP_DB_CONNECT_STRING"] == "${{ secrets.MYAPP_DB_CONNECT_STRING }}"
    assert step["env"]["K8S_SA_JSON"] == "${{ secrets.K8S_SA_JSON }}"
    assert "--set-file apps.samples.harness.secrets.asecret=$secrets_dir/" in step["run"]
    assert "--set-file apps.myapp.harness.database.connect_string=$secrets_dir/" in step["run"]
    assert "--set-file registry.secret.value=$secrets_dir/" in step["run"]
    assert 'echo "HELM_SET_ARGS=$args" >> "$GITHUB_ENV"' in step["run"]
    install = _steps(deploy, "Install chart")[0]
    assert "$HELM_SET_ARGS" in install["run"]
    assert "helm upgrade --install" in install["run"]
    # secrets only ever travel through env, never inline in a script
    assert not [run for run in _run_strings(wf) if "${{ secrets." in run]


def test_rollout_wait_and_publish_steps(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]

    rollout = _steps(jobs["wait-deployment"], "Wait for the rollouts")[0]
    lines = rollout["run"].splitlines()
    assert any(line.startswith("kubectl rollout status deployment/") for line in lines)
    assert lines[-1] == "sleep 60"

    publish = jobs["publish"]
    assert "needs.prepare.outputs.publish_tag != ''" in publish["if"]
    assert "deploy" in publish["needs"] and "tests-e2e-samples" in publish["needs"]
    assert publish["environment"] == "publish"
    # publication waits for the tests and never runs when the deployment or a test failed
    assert "needs.deploy.result == 'success'" in publish["if"]
    assert "!cancelled()" in publish["if"]
    assert "!contains(needs.*.result, 'failure')" in publish["if"]
    # the API/E2E tests run after the deployment, so they cannot block it
    assert not [n for n in jobs["deploy"]["needs"] if n.startswith(("tests-api", "tests-e2e"))]
    published = {step["name"][len("Publish "):] for step in _steps(publish, "Publish ")}
    built = {name[len("build-"):] for name in jobs if name.startswith("build-")}
    assert published == built
    step = _steps(publish, "Publish myapp")[0]
    assert step["if"] == "${{ vars.MYAPP_PUBLISH_SKIP == '' }}"
    assert step["env"]["SOURCE"] == (
        "${{ vars.REGISTRY }}/testprojectname/myapp:${{ needs.prepare.outputs.MYAPP_TAG }}"
    )
    assert step["env"]["TARGET"] == "${{ vars.REGISTRY_PUBLISH_URL || vars.REGISTRY }}/testprojectname/myapp"
    assert "imagetools create" in step["run"]


def test_prepare_command_placeholders(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    run = _step(wf["jobs"]["prepare"], "images")["run"]
    assert 'harness-deployment cloud-harness . -d "$DOMAIN"' in run
    assert "-e dev " in run
    assert "-i samples -i myapp -ex events" in run
    assert "$PATHS" not in run and "$ENV " not in run and "$PARAMS" not in run
    assert "--write-env" in run and "--force-build" in run


def test_multienv_test_overlay(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], envs=("dev", "test"))
    jobs = wf["jobs"]

    assert wf["name"] == "CloudHarness dev-test"
    assert "pull_request" in wf["on"]
    assert "publish" not in jobs
    assert jobs["prepare"]["env"]["NAMESPACE"] == "test-${{ vars.NAMESPACE_BASENAME }}"
    assert "-e dev-test " in _step(jobs["prepare"], "images")["run"]
    cleanup = jobs["cleanup"]
    assert cleanup["if"] == "${{ always() && needs.deploy.result == 'success' }}"
    assert "tests-unit-myapp" in cleanup["needs"] and "tests-e2e-samples" in cleanup["needs"]


def test_prod_deploys_only(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], envs=("prod",))
    jobs = wf["jobs"]

    assert list(jobs) == ["prepare", "deploy"]
    assert jobs["deploy"]["needs"] == ["prepare"]
    assert jobs["deploy"]["environment"] == "prod"
    # the fixture's kube_auth override lives in the dev overlay only: prod keeps the
    # default step (KUBECONFIG secret or the runner's own cluster access)
    assert [s for s in jobs["deploy"]["steps"] if s.get("name") == "Configure kubectl"]
    assert jobs["deploy"]["env"]["HELM_FLAGS"].startswith("--wait")
    assert wf["on"]["workflow_dispatch"]["inputs"]["deployment_tag"]["required"] is True


def test_stage_keeps_tests_and_tags_the_repository(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], envs=("stage",))
    jobs = wf["jobs"]

    assert not [name for name in jobs if name.startswith("build-")]
    assert "tests-api-samples" in jobs and "tests-unit-samples" not in jobs
    assert jobs["tests-api-samples"]["needs"] == ["prepare", "wait-deployment"]
    assert jobs["git-tag"]["needs"] == ["prepare", "publish"]
    assert jobs["git-tag"]["permissions"] == {"contents": "write"}
    # the tag is pushed only when the images were published: a failed deployment or test
    # skips publish, and a skipped publish must not let the guard through
    tag_if = jobs["git-tag"]["if"]
    assert "needs.publish.result == 'success'" in tag_if
    assert "needs.prepare.outputs.publish_tag != ''" in tag_if
    assert "needs.prepare.result == 'success'" in tag_if


def test_runner_configuration(tmp_path):
    wf, _ = _generate(tmp_path, ["myapp"])
    jobs = wf["jobs"]
    # the runner is a repository variable read at run time; the generation-time runner is the fallback
    default = "${{ vars.CH_GITHUB_RUNNER || '%s' }}" % DEFAULT_RUNNER
    build = "${{ vars.CH_GITHUB_BUILD_RUNNER || vars.CH_GITHUB_RUNNER || '%s' }}" % DEFAULT_RUNNER
    assert jobs["prepare"]["runs-on"] == default
    assert jobs["deploy"]["runs-on"] == default
    assert jobs["tests-unit-myapp"]["runs-on"] == default
    builds = [name for name in jobs if name.startswith("build-") and name != "build-myapp"]
    assert builds
    assert all(jobs[name]["runs-on"] == build for name in builds)
    assert jobs["build-myapp"]["runs-on"] == "big-runner", "a template runs-on is kept"

    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=CHDeployConfig(
        env="dev", includes=["myapp"], excludes=["events"], registry="reg", tag="1",
        output_path=str(tmp_path / "deployment"), ci_runner="self-hosted, linux",
    ))
    wf = project.github_actions.generate(write_on_disk=False)
    assert wf["jobs"]["prepare"]["runs-on"] == (
        """${{ vars.CH_GITHUB_RUNNER || fromJSON('["self-hosted", "linux"]') }}"""
    )


def test_workflow_invariants(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], envs=("dev", "test"))
    jobs = wf["jobs"]

    def walk(node):
        yield node
        if isinstance(node, dict):
            for value in node.values():
                yield from walk(value)
        elif isinstance(node, list):
            for value in node:
                yield from walk(value)

    for name, job in jobs.items():
        assert JOB_ID.match(name), name
        for need in job.get("needs", []):
            assert need in jobs, f"{name} needs unknown job {need}"
        if "if" in job:
            assert job["if"].startswith("${{") and job["if"].endswith("}}"), job["if"]
        assert job["steps"], name
        for step in job["steps"]:
            assert isinstance(step, dict), f"unexpanded fragment {step!r} in {name}"
            assert "uses" in step or "run" in step, step
    assert not [node for node in walk(wf) if isinstance(node, tuple)]
    assert not [node for node in walk(wf) if type(node).__module__ == "ch_cli_tools.model"]


def test_paths_are_cwd_independent(tmp_path):
    sibling_dir = tempfile.mkdtemp(dir=str(CLOUDHARNESS_ROOT.parent))
    old_cwd = os.getcwd()
    try:
        os.chdir(sibling_dir)
        wf, _ = _generate(tmp_path, ["samples"])
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(sibling_dir, ignore_errors=True)

    for name, job in wf["jobs"].items():
        if not name.startswith("build-"):
            continue
        context = _step(job, "build")["with"]["context"]
        assert not context.startswith("./..") and "/../" not in context, (name, context)
        assert not os.path.isabs(context), (name, context)
    assert "../cloud-harness" not in _step(wf["jobs"]["prepare"], "images")["run"]


def test_generate_writes_the_workflow_under_github_workflows(tmp_path):
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
    project.github_actions.generate()

    workflow = tmp_path / ".github" / "workflows" / "cloudharness-dev.yaml"
    assert workflow.exists()
    text = workflow.read_text()
    assert text.startswith("name: CloudHarness dev\n") and text.splitlines()[1].startswith("on:")
    assert "build-args: |" in text, "multi-line inputs are written as literal blocks"
    assert "run: |" in text
    loaded = YAML(typ="safe").load(text)
    assert "on" in loaded and "build-myapp" in loaded["jobs"]


def test_no_template_means_no_workflow(tmp_path):
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
    project = chain(tmp_path, config=CHDeployConfig(env="dev", registry="reg", tag="1"))
    assert project.github_actions.generate() == {}
    assert not (tmp_path / ".github").exists()
