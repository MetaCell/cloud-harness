"""End-to-end tests of the GitHub Actions workflow generator, over the same
[CLOUDHARNESS_ROOT, RESOURCES] chain and arguments test_codefresh.py uses."""

import os
import re
import shutil
import tempfile

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain
from ruamel.yaml import YAML
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig, ci
from ch_cli_tools.api import create_helm_chart
from ch_cli_tools.github_actions import DEFAULT_RUNNER, referenced_names

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
    assert wf["jobs"]["tests-api-samples"]["runs-on"] == "big-runner"
    # the generator-only section is consumed, not emitted; its kube_auth steps replace
    # the default ones wherever a job asks for $KUBE_AUTH
    assert "cloudharness" not in wf
    steps = wf["jobs"]["deploy"]["steps"]
    assert [s for s in steps if s.get("name") == "Custom cluster access"]
    assert not [s for s in steps if s.get("name") == "Configure kubectl"]
    assert wf["jobs"]["deploy"]["environment"] == "dev"
    # OIDC tokens are not minted for every job
    assert "id-token" not in wf["permissions"]


def test_prepare_builds_the_missing_images_with_skaffold(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]
    prepare = jobs["prepare"]

    # one job builds every image: harness-deployment lists the missing ones, skaffold builds them
    assert not [name for name in jobs if name.startswith("build")]
    assert "--write-env --write-skaffold-ci" in _step(prepare, "images")["run"]
    build = _steps(prepare, "Build and push the images")[0]
    assert build["run"].startswith(
        "skaffold build --filename deployment/skaffold-ci.yaml --cache-artifacts=false"
    )
    assert build["env"] == {
        "NOCACHE": "${{ github.run_id }}",
        "CH_BRANCH_TAG": "${{ steps.env.outputs.branch_tag }}",
    }
    names = [step.get("name") or step.get("uses") for step in prepare["steps"]]
    assert names.index("Prepare helm chart") < names.index("Install skaffold") < names.index(
        "Build and push the images"
    ) < names.index("Run the unit tests")
    login = next(step for step in prepare["steps"] if step.get("uses") == "docker/login-action@v3")
    assert login["with"]["registry"] == "${{ steps.env.outputs.registry_host }}"
    install = _steps(prepare, "Install skaffold")[0]
    assert re.fullmatch(r"v\d+\.\d+\.\d+", install["env"]["SKAFFOLD_VERSION"])
    assert re.fullmatch(r"[0-9a-f]{64}", install["env"]["SKAFFOLD_SHA256"])
    assert 'sha256sum -c -' in install["run"]
    # the merged contexts never leave prepare: the only artifact is the deployment
    uploads = [step for step in prepare["steps"] if step.get("uses") == "actions/upload-artifact@v4"]
    assert [step["with"]["name"] for step in uploads] == ["cloudharness-deployment"]
    assert jobs["deploy"]["needs"][0] == "prepare"


def test_git_dependency_checkouts(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    prepare = wf["jobs"]["prepare"]

    clones = [step for step in _steps(prepare, "Clone ") if step["name"] != "Clone cloud-harness"]
    assert len(clones) == 2, "myapp declares two git dependencies"
    assert clones[0]["uses"] == "actions/checkout@v4"
    assert clones[0]["with"]["repository"] == "a/b"
    assert clones[0]["with"]["ref"] == "master"
    assert clones[0]["with"]["path"] == "applications/myapp/dependencies/b"
    # cloned before harness-deployment merges and hashes the build contexts
    step_names = [step.get("name") for step in prepare["steps"]]
    assert step_names.index("Clone b") < step_names.index("Prepare helm chart")
    for name, job in wf["jobs"].items():
        if name != "prepare":
            assert not [s for s in _steps(job, "Clone ") if s["name"] != "Clone cloud-harness"], name


def test_cloudharness_is_cloned_by_projects_only(tmp_path):
    # a project's jobs clone cloud-harness (CLOUDHARNESS_BRANCH, default develop) and install its tools
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    prepare = wf["jobs"]["prepare"]["steps"]
    [clone] = [step for step in prepare if step.get("name") == "Clone cloud-harness"]
    assert clone["with"] == {
        "repository": "MetaCell/cloud-harness",
        "ref": "${{ vars.CLOUDHARNESS_BRANCH || 'develop' }}",
        "path": "cloud-harness",
    }
    assert _steps(wf["jobs"]["prepare"], "Install cloud-harness tools")[0]["run"] == (
        "bash cloud-harness/install.sh"
    )
    assert _steps(wf["jobs"]["tests-api-samples"], "Clone cloud-harness")

    # cloud-harness' own workflow tests the branch that triggered it, tools included: it never
    # clones another branch nor reads CLOUDHARNESS_BRANCH
    project = chain(
        CLOUDHARNESS_ROOT,
        config=CHDeployConfig(env="test", includes=["samples"], output_path=str(tmp_path / "deployment")),
    )
    wf = project.github_actions.generate(write_on_disk=False)
    assert "CLOUDHARNESS_BRANCH" not in referenced_names(wf)["vars"]
    assert "CLOUDHARNESS_BRANCH" not in wf.get("env", {})
    assert not [
        name for name, job in wf["jobs"].items() if _steps(job, "Clone cloud-harness")
    ]
    assert _steps(wf["jobs"]["prepare"], "Install cloud-harness tools")[0]["run"] == "bash ./install.sh"


def test_prepare_outputs_cover_every_image(tmp_path):
    wf, project = _generate(tmp_path, ["samples", "myapp"])
    outputs = wf["jobs"]["prepare"]["outputs"]

    assert list(outputs)[0] == "branch_tag", "template outputs come first"
    names = [*ci.build_entities(project), *ci.test_runner_images(project)]
    assert "cloudharness-base" in names and "test-api" in names
    for name in names:
        variable = ci.tag_variable(name)
        assert outputs[variable] == "${{ steps.images.outputs.%s }}" % variable
        assert outputs[f"{variable}_EXISTS"] == "${{ steps.images.outputs.%s_EXISTS }}" % variable
    # instances share their parent's image but still get their variables
    assert "MYAPP_INST1_TAG" in outputs


def test_unit_tests_run_in_prepare_with_skaffold(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]

    # skaffold runs every app's unit tests (the `test` section of deployment/skaffold-ci.yaml)
    # against every image of the deployment, rebuilt or not: no job of their own
    assert not [name for name in jobs if name.startswith("tests-unit")]
    step = _steps(jobs["prepare"], "Run the unit tests")[0]
    assert step["run"].startswith(
        "skaffold test --filename deployment/skaffold-ci.yaml "
        "--build-artifacts deployment/skaffold-images.json"
    )
    # the deployment waits for them, as the Codefresh unittest stage precedes deploy
    assert jobs["deploy"]["needs"] == ["prepare"]


def test_api_and_e2e_test_jobs(tmp_path):
    wf, _ = _generate(tmp_path, ["samples"])
    jobs = wf["jobs"]

    api = jobs["tests-api-samples"]
    assert api["needs"] == ["prepare", "deploy"]
    assert api["steps"][0] == {"name": "Give the certificates time to settle", "run": "sleep 60"}
    assert "needs.prepare.outputs.skip_tests != 'true'" in api["if"]
    # skaffold deploy waits for the rollout: the deployment must have succeeded
    assert "needs.deploy.result == 'success'" in api["if"]
    assert "!contains(needs.*.result, 'failure')" in api["if"]
    step = _steps(api, "Run samples API tests")[0]
    assert step["env"]["APP_URL"] == "https://www.${{ vars.DOMAIN }}/api"
    assert step["env"]["CH_TEST_IMAGE"] == (
        "${{ vars.REGISTRY }}/testprojectname/test-api:${{ needs.prepare.outputs.TEST_API_TAG }}"
    )
    assert "-e APP_URL" in step["run"]
    assert '-v "$GITHUB_WORKSPACE/cloud-harness/applications/samples:/home/test"' in step["run"]
    assert "/opt/cloudharness/resources/allvalues.yaml" in step["run"]
    assert {"name": "cloudharness-deployment", "path": "deployment"} in [
        s["with"] for s in api["steps"] if s.get("uses") == "actions/download-artifact@v4"
    ], "the mounted values.yaml comes from the deployment artifact"
    assert "-w /home/test" in step["run"]
    commands = step["env"]["CH_TEST_COMMANDS"].splitlines()
    assert "--pre-run cloudharness_test.apitest_init" in commands[1]
    assert "--base-url https://www.${{ vars.DOMAIN }}/api" in commands[1]
    assert commands[2] == "pytest -v test/api"

    e2e = jobs["tests-e2e-samples"]
    assert e2e["needs"] == ["prepare", "deploy"]
    step = _steps(e2e, "Run samples E2E tests")[0]
    assert step["env"]["APP_URL"] == "https://www.${{ vars.DOMAIN }}"
    assert (
        '-v "$GITHUB_WORKSPACE/cloud-harness/applications/samples/test/e2e:/home/test/__tests__/samples"'
        in step["run"]
    )
    assert step["env"]["CH_TEST_COMMANDS"] == "set -e\nnpx puppeteer browsers install chrome\nyarn test\n"
    assert "commands" not in e2e, "the prototype's commands key never reaches the workflow"


def test_no_api_e2e_jobs_when_not_enabled(tmp_path):
    wf, _ = _generate(tmp_path, ["myapp"])
    names = list(wf["jobs"])
    assert not [n for n in names if n.startswith(("tests-api", "tests-e2e", "build-test-"))]
    assert "deploy" in names
    # nothing references the removed prototypes any more
    for job in wf["jobs"].values():
        for need in job.get("needs", []):
            assert need in wf["jobs"], need


def test_deploy_with_skaffold(tmp_path):
    wf, project = _generate(tmp_path, ["samples", "myapp"], registry_secret_name="my-pull-secret")
    jobs = wf["jobs"]
    deploy = jobs["deploy"]

    # skaffold deploy installs the chart and waits for its rollout: no job of its own waits for it
    assert "wait-deployment" not in jobs
    run = _steps(deploy, "Deploy and wait for the rollout")[0]["run"]
    assert run.startswith(
        "skaffold deploy --filename deployment/skaffold-ci.yaml --build-artifacts deployment/skaffold-images.json "
    )
    # skaffold labels every pod template with its run id: a new one would restart every pod on every deploy
    assert "--label skaffold.dev/run-id=cloudharness" in run
    names = [step.get("name") or step.get("uses") for step in deploy["steps"]]
    assert names.index("Write the secret values") < names.index("Deploy and wait for the rollout")
    assert names.index("Install skaffold") < names.index("Deploy and wait for the rollout")

    # every secret value lands in the file skaffold-ci.yaml passes to helm with --set-file
    step = _steps(deploy, "Write the secret values")[0]
    assert step["env"]["ASECRET"] == "${{ secrets.ASECRET }}"
    assert step["env"]["MYAPP_DB_CONNECT_STRING"] == "${{ secrets.MYAPP_DB_CONNECT_STRING }}"
    assert step["env"]["K8S_SA_JSON"] == "${{ secrets.K8S_SA_JSON }}"
    assert 'secrets_dir="$HOME/.cloudharness/secrets"' in step["run"]
    plan = project.skaffold_ci.generate({}, write_on_disk=False)
    set_files = plan["deploy"]["helm"]["releases"][0]["setFiles"]
    assert set_files["registry.secret.value"] == "~/.cloudharness/secrets/K8S_SA_JSON"
    for path in set_files.values():
        file_name = path[len("~/.cloudharness/secrets/"):]
        assert f'"$secrets_dir/{file_name}"' in step["run"], file_name
    assert step["run"].count('"$secrets_dir/ASECRET"') == 1, "a secret is written once"
    # secrets only ever travel through env, never inline in a script
    assert not [run for run in _run_strings(wf) if "${{ secrets." in run]


def test_promote_workflow(tmp_path):
    wf, project = _generate(tmp_path, ["samples", "myapp"])
    # the dev pipeline publishes nothing itself: a run is promoted by hand afterwards
    assert "publish" not in wf["jobs"]
    assert "publish_tag" not in wf["on"]["workflow_dispatch"]["inputs"]
    assert "publish_tag" not in wf["jobs"]["prepare"]["outputs"]
    # the API/E2E tests run after the deployment, so they cannot block it
    assert not [n for n in wf["jobs"]["deploy"]["needs"] if n.startswith(("tests-api", "tests-e2e"))]

    promote = project.github_actions.promote
    assert promote["name"] == "CloudHarness promote"
    inputs = promote["on"]["workflow_dispatch"]["inputs"]
    assert inputs["tag"]["required"] is True and inputs["run_id"]["default"] == ""
    assert promote["permissions"] == {"contents": "write", "actions": "read"}
    [job] = promote["jobs"].values()
    # promotion waits for the approval of the `publish` environment
    assert job["environment"] == "publish"
    assert job["runs-on"] == "${{ vars.CH_GITHUB_RUNNER || '%s' }}" % DEFAULT_RUNNER
    # it promotes runs of the workflow generated with it, by default its latest successful one
    find = _steps(job, "Find the run to promote")[0]["run"]
    assert project.github_actions.file_path.name == "ci--samples-myapp--dev.yaml"
    assert "--workflow ci--samples-myapp--dev.yaml " in find and "$WORKFLOW" not in find
    # the exact images of that run: the skaffold-images.json of its deployment artifact
    download = _steps(job, "Download the images of the run")[0]["with"]
    assert download["run-id"] == "${{ steps.run.outputs.id }}" and download["name"] == "cloudharness-deployment"
    tag = _steps(job, "Tag the images")[0]["run"]
    assert "deployment/skaffold-images.json" in tag and "docker buildx imagetools create" in tag
    # the git tag goes on the run's commit, pushed with a token that can start the staging pipeline
    checkout = next(step for step in job["steps"] if step.get("uses") == "actions/checkout@v4")
    assert checkout["with"] == {
        "ref": "${{ steps.run.outputs.sha }}",
        "token": "${{ secrets.GH_PAT || github.token }}",
    }
    assert 'git push origin "refs/tags/$TAG"' in _steps(job, "Tag the repository")[0]["run"]

    # written next to the workflow, and only by the dev pipeline
    project.github_actions.generate(output_path=tmp_path / "workflows")
    assert sorted(path.name for path in (tmp_path / "workflows").iterdir()) == [
        "ci--samples-myapp--dev.yaml",
        "ci--samples-myapp--promote.yaml",
    ]
    _, test_project = _generate(tmp_path, ["samples"], envs=("test",))
    assert test_project.github_actions.promote is None


def test_prepare_command_placeholders(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    run = _step(wf["jobs"]["prepare"], "images")["run"]
    assert 'harness-deployment cloud-harness . -d "$DOMAIN"' in run
    assert "-e dev " in run
    assert "-i samples -i myapp -ex events" in run
    assert "$PATHS" not in run and "$ENV " not in run and "$PARAMS" not in run
    assert "--write-env" in run and "--write-skaffold-ci" in run and "--force-build" in run


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
    # deleting the deployment waits for the `cleanup` environment's approval, without recording a deployment
    assert cleanup["environment"] == {"name": "cleanup", "deployment": False}
    assert jobs["deploy"]["environment"] == "dev-test"
    assert "tests-api-samples" in cleanup["needs"] and "tests-e2e-samples" in cleanup["needs"]


def test_prod_deploys_only(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], envs=("prod",))
    jobs = wf["jobs"]

    assert list(jobs) == ["prepare", "deploy"]
    # prod deploys promoted images: prepare builds nothing, on the default runner
    assert jobs["prepare"]["name"] == "Prepare helm chart"
    assert not _steps(jobs["prepare"], "Build and push")
    assert jobs["prepare"]["runs-on"] == "${{ vars.CH_GITHUB_RUNNER || '%s' }}" % DEFAULT_RUNNER
    assert jobs["deploy"]["needs"] == ["prepare"]
    assert jobs["deploy"]["environment"] == "prod"
    # the fixture's kube_auth override lives in the dev overlay only: prod keeps the
    # default step (KUBECONFIG secret or the runner's own cluster access)
    assert [s for s in jobs["deploy"]["steps"] if s.get("name") == "Configure kubectl"]
    assert _steps(jobs["deploy"], "Deploy and wait for the rollout")
    assert wf["on"]["workflow_dispatch"]["inputs"]["deployment_tag"]["required"] is True


def test_stage_deploys_the_tag_that_started_it(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"], envs=("stage",))
    jobs = wf["jobs"]

    # the promote workflow pushes a git tag: the staging pipeline deploys the images with that tag
    assert wf["on"]["push"] == {"tags": ["*"]}
    assert wf["on"]["workflow_dispatch"]["inputs"]["deployment_tag"]["required"] is True
    assert "github.ref_type == 'tag' && github.ref_name" in jobs["prepare"]["env"]["DEPLOYMENT_TAG"]
    assert not _steps(jobs["prepare"], "Build and push"), "stage deploys promoted images"
    assert not _steps(jobs["prepare"], "Run the unit tests"), "stage runs no unit tests"
    assert "tests-api-samples" in jobs
    assert jobs["tests-api-samples"]["needs"] == ["prepare", "deploy"]
    assert "publish" not in jobs and "git-tag" not in jobs


def test_runner_configuration(tmp_path):
    wf, _ = _generate(tmp_path, ["samples", "myapp"])
    jobs = wf["jobs"]
    # the runner is a repository variable read at run time; the generation-time runner is the fallback
    default = "${{ vars.CH_GITHUB_RUNNER || '%s' }}" % DEFAULT_RUNNER
    build = "${{ vars.CH_GITHUB_BUILD_RUNNER || vars.CH_GITHUB_RUNNER || '%s' }}" % DEFAULT_RUNNER
    assert jobs["prepare"]["runs-on"] == build, "prepare builds the images"
    assert jobs["deploy"]["runs-on"] == default
    assert jobs["tests-e2e-samples"]["runs-on"] == default
    assert jobs["tests-api-samples"]["runs-on"] == "big-runner", "a template runs-on is kept"

    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=CHDeployConfig(
        env="dev", includes=["myapp"], excludes=["events"], registry="reg", tag="1",
        output_path=str(tmp_path / "deployment"), ci_runner="self-hosted, linux",
    ))
    wf = project.github_actions.generate(write_on_disk=False)
    assert wf["jobs"]["prepare"]["runs-on"] == (
        """${{ vars.CH_GITHUB_BUILD_RUNNER || vars.CH_GITHUB_RUNNER || fromJSON('["self-hosted", "linux"]') }}"""
    )
    assert wf["jobs"]["deploy"]["runs-on"] == (
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
        wf, _ = _generate(tmp_path, ["samples", "myapp"])
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(sibling_dir, ignore_errors=True)

    prepare = wf["jobs"]["prepare"]
    paths = [step["with"]["path"] for step in _steps(prepare, "Clone ")]
    assert "applications/myapp/dependencies/b" in paths
    for path in paths:
        assert not path.startswith("..") and "/../" not in path and not os.path.isabs(path), path
    assert "../cloud-harness" not in _step(prepare, "images")["run"]


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

    workflow = tmp_path / ".github" / "workflows" / "ci--all--dev.yaml"
    assert workflow.exists()
    text = workflow.read_text()
    assert text.startswith("name: CloudHarness dev\n") and text.splitlines()[1].startswith("on:")
    assert "run: |" in text, "multi-line strings are written as literal blocks"
    loaded = YAML(typ="safe").load(text)
    assert "on" in loaded and "prepare" in loaded["jobs"]


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
