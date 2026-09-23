"""Ports of the legacy ch_cli_tools structural tests onto the ch_cli_tools.ng model.

Only tests about project/app structure (discovery, naming, Dockerfile parsing) are
ported here - not generator output. See tests/test_utils.py and tests/test_helm.py
for the originals.
"""

from pathlib import Path

import pytest
from ch_cli_tools.ng import CHDeployConfig, CHProject
from ch_cli_tools.ng.model import DependencyUnknownError
from ch_cli_tools.ng.skaffold import CHSkaffold

HERE = Path(__file__).parent
RESOURCES = HERE / "resources"
CLOUDHARNESS_ROOT = HERE.parent.parent.parent
WRONG_DEPENDENCIES = RESOURCES / "wrong-dependencies"


@pytest.fixture(scope="module")
def resources_project():
    return CHProject(RESOURCES, config=CHDeployConfig())


def test_base_images_missing_dockerfile(resources_project):
    # accounts has no Dockerfile at all in this fixture tree.
    assert resources_project["accounts"].dockerfile.base_images == {}


def test_base_images_no_arg_based_from(resources_project):
    # dependantapp/Dockerfile: `ARG MYAPP` has no `=value`, so it's never recorded,
    # and `FROM $MYAPP` can't resolve it.
    assert resources_project["dependantapp"].dockerfile.base_images == {}


def test_base_images_with_arg_based_from(resources_project):
    # newapp1/Dockerfile: two ARG-defaulted bases actually used in a FROM
    # (${mybase} and $mybase2 forms), one ARG left unused by any FROM.
    base_images = resources_project["newapp1"].dockerfile.base_images
    assert base_images == {"mybase": "foo:bar", "mybase2": "spam:egg"}
    assert "mybase3" not in base_images


def test_app_and_task_dockerfiles_are_found(resources_project):
    app = resources_project["myapp"]

    assert app.dockerfile.exists()
    assert app.dockerfile.path.name == "Dockerfile"

    task = app.tasks["myapp-mytask"]
    assert task.dockerfile.exists()
    assert task.dockerfile.path == app.path / "tasks" / "mytask" / "Dockerfile"


def _minimal_project(tmp_path, registry=""):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    (app_dir / "tasks" / "mytask").mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "tasks" / "mytask" / "Dockerfile").write_text("FROM scratch\n")

    return CHProject(
        root, cloudharness_path=root, config=CHDeployConfig(registry=registry)
    )


def test_app_and_task_image_names(tmp_path):
    project = _minimal_project(tmp_path)
    app = project["myapp"]

    assert app.image_name == "testproj/myapp"
    assert app.tasks["myapp-mytask"].image_name == "testproj/myapp-mytask"


def test_qualify_prefixes_registry(tmp_path):
    project = _minimal_project(tmp_path, registry="reg")
    app = project["myapp"]
    skaffold = CHSkaffold(tmp_path / "skaffold.yaml", project)

    assert skaffold.qualify(app.image_name) == "reg/testproj/myapp"


def test_no_include_means_every_scanned_app_is_entrypoint():
    project = CHProject(
        RESOURCES, cloudharness_path=CLOUDHARNESS_ROOT, config=CHDeployConfig()
    )

    assert set(project.entrypoint_apps().keys()) == set(project.scanned_apps.keys())
    assert "jupyterhub" in project.entrypoint_apps()


def test_include_exclude_and_transitive_dependencies():
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["samples", "myapp"], excludes=["events"]),
    )

    entrypoints = set(project.entrypoint_apps().keys())
    assert entrypoints == {"samples", "myapp"}

    involved = {a if isinstance(a, str) else a.name for a in project.involved_apps}

    # Not included, not a dependency of anything included.
    assert "jupyterhub" not in involved

    # First-level dependencies: samples --soft--> accounts, myapp --soft--> legacy.
    assert "accounts" in involved
    assert "legacy" in involved

    # Second-level: samples --soft--> workflows --hard--> argo. Only resolvable
    # once cross-root app merging works - workflows only has a real
    # dependencies.hard in cloud-harness's copy, not the fixture's.
    assert "argo" in involved

    # Explicit exclude removes it even though samples soft-depends on it.
    assert "events" not in involved


def test_same_named_app_in_both_roots_is_layered_not_replaced():
    project = CHProject(
        RESOURCES, cloudharness_path=CLOUDHARNESS_ROOT, config=CHDeployConfig()
    )
    workflows = project["workflows"]

    # The project's own copy is still the identity/override path...
    assert workflows.path == RESOURCES / "applications" / "workflows"
    # ...but cloud-harness's copy is known too, as the default to merge with.
    assert workflows.default.path == CLOUDHARNESS_ROOT / "applications" / "workflows"

    # Both sides' tasks are present: the fixture's own plus cloud-harness's three.
    assert set(workflows.tasks.keys()) == {
        "workflows-new-task",
        "workflows-notify-queue",
        "workflows-extract-download",
        "workflows-send-result-event",
    }

    # cloud-harness's real `dependencies.hard: [argo]` survives the override, since
    # the fixture's values.yaml (which doesn't exist) has nothing to say about it.
    assert [d.name for d in workflows.hard_dependencies] == ["argo"]


def test_same_app_values_precedence_across_roots_and_env():
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["events"], env="prod"),
    )
    limits = project["events"].all_values()["kafka"]["resources"]["limits"]

    # RESOURCES's own values.yaml sets `memory: overridden`; its values-prod.yaml
    # doesn't touch memory at all - so this can only be "overridden" if the
    # project's base values.yaml is consulted even when an env-specific file
    # exists, not just the (cloud-harness real) values-prod.yaml alone.
    assert limits["memory"] == "overridden"

    # RESOURCES's own values-prod.yaml sets `cpu: overridden-prod`, which must win
    # over both cloud-harness's values-prod.yaml (cpu: 500m) and RESOURCES's own
    # base values.yaml (cpu: 600m) - the project's env layer is the most specific
    # source there is.
    assert limits["cpu"] == "overridden-prod"


# Not a port - covers the third facet of the same fix: when the project's own copy
# of an app has no Dockerfile of its own, its cloud-harness default is used instead
# of the app silently ending up with no Dockerfile at all.
def test_app_dockerfile_falls_back_to_cloudharness_default(tmp_path):
    ch = tmp_path / "ch"
    proj = tmp_path / "proj"
    (ch / "applications" / "myapp").mkdir(parents=True)
    (ch / "applications" / "myapp" / "Dockerfile").write_text("FROM scratch\n")
    (proj / "applications" / "myapp" / "deploy").mkdir(parents=True)
    (proj / "applications" / "myapp" / "deploy" / "values.yaml").write_text("a: 1\n")
    (proj / "deployment-configuration").mkdir(parents=True)
    (proj / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )

    project = CHProject(proj, cloudharness_path=ch, config=CHDeployConfig())
    app = project["myapp"]

    assert app.dockerfile.exists()
    assert app.dockerfile.path == ch / "applications" / "myapp" / "Dockerfile"


# Ports test_helm.py::test_collect_helm_values_harness_image_name_override.
def test_harness_image_name_overrides_dockerfile_derived_name():
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], env="imagename"),
    )
    app = project["myapp"]

    assert app.image_name == "testprojectname/custom-myapp"
    assert app.tasks["myapp-mytask"].image_name == "testprojectname/custom-myapp-mytask"


def test_unresolved_hard_dependency_raises():
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-hard"])
    )
    with pytest.raises(DependencyUnknownError):
        project.all_values()


def test_unresolved_soft_dependency_currently_also_raises():
    # Old behavior: does NOT raise (dependencies.soft is optional by design). `ng`
    # doesn't distinguish soft from hard once the name is in `involved_apps` -
    # known gap.
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-soft"])
    )
    with pytest.raises(DependencyUnknownError):
        project.all_values()


def test_unresolved_build_dependency_currently_does_not_raise():
    # Old behavior: DOES raise. `ng`'s CHProject.all_dependencies() never walks
    # build_dependencies, so an unresolved build dep never reaches `involved_apps`
    # at all - known gap.
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-build"])
    )
    project.all_values()  # does not raise
