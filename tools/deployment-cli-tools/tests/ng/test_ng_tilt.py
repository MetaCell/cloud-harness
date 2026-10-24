"""ch_cli_tools.ng.tilt generator tests. See test_ng.py (this folder) for the
structural/model tests these build on, and ch_cli_tools/ng/tilt.py's own
module docstring for the generation algorithm.
"""

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain
from test_util_ng import write_tree_from_yaml

from ch_cli_tools.ng import CHDeployConfig, CHProject


def _tilt_project(
    tmp_path, *, subdomain="mysubdomain", service_auto=True, deployment_auto=False
):
    write_tree_from_yaml(
        tmp_path,
        f"""
        deployment-configuration:
          values-template.yaml: |
            name: testproj
            mainapp: myapp
        applications:
          myapp:
            Dockerfile: |
              FROM scratch
            tasks:
              mytask:
                Dockerfile: |
                  FROM scratch
            deploy:
              values.yaml: |
                harness:
                  subdomain: {subdomain}
                  service:
                    auto: {str(service_auto).lower()}
                  deployment:
                    auto: {str(deployment_auto).lower()}
    """,
    )
    return CHProject(tmp_path, config=CHDeployConfig())


def test_app_artifact_has_build_args_and_source_images(tmp_path):
    project = _tilt_project(tmp_path)
    images = {a["app_key"]: a for a in project.tilt._collect_artifacts().values()}

    myapp = images["myapp"]
    assert myapp["image"] == "testproj/myapp"
    assert myapp["docker"]["dockerfile"].endswith("Dockerfile")
    assert myapp["docker"]["buildArgs"] == {}


def test_task_artifact_is_marked_is_task(tmp_path):
    project = _tilt_project(tmp_path)
    images = {a["app_key"]: a for a in project.tilt._collect_artifacts().values()}

    task = images["myapp-mytask"]
    assert task["is_task"] is True
    assert task["is_app"] is False
    assert task["parent_app_name"] == "myapp"


def test_is_app_driven_by_service_auto_not_deployment_auto(tmp_path):
    project = _tilt_project(tmp_path, service_auto=False, deployment_auto=True)
    images = {a["app_key"]: a for a in project.tilt._collect_artifacts().values()}
    assert images["myapp"]["is_app"] is False

    project = _tilt_project(tmp_path, service_auto=True, deployment_auto=False)
    images = {a["app_key"]: a for a in project.tilt._collect_artifacts().values()}
    assert images["myapp"]["is_app"] is True


def test_rendered_tiltfile_groups_task_under_parent_app_key_even_when_subdomain_differs(
    tmp_path,
):
    # myapp's Tilt UI link uses its subdomain ("totallydifferent"), but the
    # extra_env grouping below must still key off the stable app_key ("myapp") -
    # legacy itself matched against the subdomain-swapped display name here,
    # which silently breaks this grouping whenever subdomain != app name.
    project = _tilt_project(tmp_path, subdomain="totallydifferent")
    tiltfile = project.tilt.generate(write_on_disk=False)

    assert 'extra_env.setdefault("myapp", [])' in tiltfile
    assert 'extra_env["myapp"].append("testproj/myapp-mytask")' in tiltfile
    assert "link('http://totallydifferent." in tiltfile
    assert "k8s_resource(\n    'myapp'," in tiltfile


def test_task_build_sets_match_in_env_vars(tmp_path):
    project = _tilt_project(tmp_path)
    tiltfile = project.tilt.generate(write_on_disk=False)
    assert "ref='testproj/myapp-mytask'" in tiltfile
    assert (
        "match_in_env_vars=True"
        in tiltfile.split("ref='testproj/myapp-mytask'")[1].split("\n")[0]
    )
    assert (
        "match_in_env_vars=True"
        not in tiltfile.split("ref='testproj/myapp'")[1].split("\n")[0]
    )


def test_base_images_are_always_included_even_without_a_deployed_dependent():
    # cloudharness-base/my-common etc. must appear regardless of whether any
    # currently-included app actually depends on them - matches legacy's own
    # unconditional base/static-image scan.
    project = chain(
        CLOUDHARNESS_ROOT, RESOURCES, config=CHDeployConfig(includes=["events"])
    )
    artifacts = project.tilt._collect_artifacts()
    assert "cloudharness-base" in artifacts
    assert "my-common" in artifacts


def test_write_on_disk_writes_plain_text_tiltfile(tmp_path):
    project = _tilt_project(tmp_path)
    out = tmp_path / "out"
    project.tilt.generate(output_path=str(out))

    written = (out / "Tiltfile").read_text()
    assert written.startswith("load(")
    assert "docker_build(ref='testproj/myapp'" in written
