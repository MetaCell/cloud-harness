"""Ports of the legacy ch_cli_tools structural tests onto the ch_cli_tools.ng model.

Only tests about project/app structure (discovery, naming, Dockerfile parsing) are
ported here - not generator output. See test_ng_skaffold.py (this folder) for the
skaffold generator tests, and tests/test_utils.py/tests/test_helm.py for the
originals.
"""

import pytest
from ch_cli_tools.ng import CHDeployConfig, CHProject
from ch_cli_tools.ng.model import DependencyUnknownError
from ch_cli_tools.ng.skaffold import CHSkaffold
from conftest import (
    CLOUDHARNESS_ROOT,
    RESOURCES,
    WRONG_DEPENDENCIES,
    chain,
    minimal_project,
)


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


def test_app_and_task_image_names(tmp_path):
    project = minimal_project(tmp_path)
    app = project["myapp"]

    assert app.image_name == "testproj/myapp"
    assert app.tasks["myapp-mytask"].image_name == "testproj/myapp-mytask"


def test_qualify_prefixes_registry(tmp_path):
    project = minimal_project(tmp_path, registry="reg")
    app = project["myapp"]
    skaffold = CHSkaffold(tmp_path / "skaffold.yaml", project)

    assert skaffold.qualify(app.image_name) == "reg/testproj/myapp"


def test_no_include_means_every_scanned_app_is_entrypoint():
    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=CHDeployConfig())

    assert set(project.entrypoint_apps().keys()) == set(project.scanned_apps.keys())
    assert "jupyterhub" in project.entrypoint_apps()


def test_include_exclude_and_transitive_dependencies():
    project = chain(
        CLOUDHARNESS_ROOT,
        RESOURCES,
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

    # Second-level: samples --soft--> workflows --hard--> argo. This only resolves
    # because cross-root app merging is in place - workflows only has a real
    # dependencies.hard in cloud-harness's copy, not the fixture's, so this
    # assertion exercises that merge, not just soft/hard closure on its own.
    assert "argo" in involved

    # Explicit exclude removes it even though samples soft-depends on it.
    assert "events" not in involved


def test_same_named_app_in_both_roots_is_layered_not_replaced():
    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=CHDeployConfig())
    workflows = project["workflows"]

    # The project's own copy is still the identity/override path...
    assert workflows.path == RESOURCES / "applications" / "workflows"
    # ...but cloud-harness's copy is known too, as the default to merge with.
    assert workflows.base.path == CLOUDHARNESS_ROOT / "applications" / "workflows"

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
    project = chain(
        CLOUDHARNESS_ROOT,
        RESOURCES,
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

    project = chain(ch, proj, config=CHDeployConfig())
    app = project["myapp"]

    assert app.dockerfile.exists()
    assert app.dockerfile.path == ch / "applications" / "myapp" / "Dockerfile"


# Not a port - no legacy test actually constructs this layout in isolation
# (tests/test_utils.py::test_find_dockerfile_paths only covers the top-level
# + tasks/ cases); legacy's own directory walk only ever got exercised here
# incidentally, by real apps (workflows, common, notifications, volumemanager)
# happening to use this layout in the real checkout. Multi-component apps
# (an API spec, a frontend, and the actual backend service) put the
# Dockerfile one level down, under a conventional subdirectory name, to keep
# it separate from sibling non-Docker concerns at the app's top level.
def test_app_dockerfile_found_under_a_conventional_subdirectory(tmp_path):
    app_dir = tmp_path / "applications" / "myapp"
    (app_dir / "server").mkdir(parents=True)
    (app_dir / "server" / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "deployment-configuration").mkdir(parents=True)
    (tmp_path / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )

    project = CHProject(tmp_path, config=CHDeployConfig())
    app = project["myapp"]

    assert app.dockerfile.exists()
    assert app.dockerfile.path == app_dir / "server" / "Dockerfile"


def test_app_dockerfile_prefers_top_level_over_a_conventional_subdirectory(tmp_path):
    app_dir = tmp_path / "applications" / "myapp"
    (app_dir / "server").mkdir(parents=True)
    (app_dir / "server" / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "deployment-configuration").mkdir(parents=True)
    (tmp_path / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )

    project = CHProject(tmp_path, config=CHDeployConfig())
    app = project["myapp"]

    assert app.dockerfile.path == app_dir / "Dockerfile"


def test_app_dockerfile_picks_shortest_path_among_equal_depth_candidates(tmp_path):
    # No real app nests more than one of these at once, and nothing writes an
    # explicit priority between them - this only pins down the deterministic
    # tiebreak (alphabetical), not a meaningful real-world precedence.
    app_dir = tmp_path / "applications" / "myapp"
    (app_dir / "backend").mkdir(parents=True)
    (app_dir / "backend" / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "src").mkdir(parents=True)
    (app_dir / "src" / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "deployment-configuration").mkdir(parents=True)
    (tmp_path / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )

    project = CHProject(tmp_path, config=CHDeployConfig())
    app = project["myapp"]

    assert app.dockerfile.path == app_dir / "backend" / "Dockerfile"


def test_app_dockerfile_ignores_tasks_subtree(tmp_path):
    # tasks/ is a structural concept of its own (CHAppTask) - a task's
    # Dockerfile must never be picked up as the owning app's own.
    app_dir = tmp_path / "applications" / "myapp"
    (app_dir / "tasks" / "mytask").mkdir(parents=True)
    (app_dir / "tasks" / "mytask" / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "deployment-configuration").mkdir(parents=True)
    (tmp_path / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )

    project = CHProject(tmp_path, config=CHDeployConfig())
    app = project["myapp"]

    assert not app.dockerfile.exists()


# Ports test_helm.py::test_collect_helm_values_harness_image_name_override.
def test_harness_image_name_overrides_dockerfile_derived_name():
    project = chain(
        CLOUDHARNESS_ROOT,
        RESOURCES,
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


def test_unresolved_soft_dependency_does_not_raise():
    # A soft dependency is optional by design: unresolved is never fatal, matching
    # the old validate_dependencies (warns, doesn't raise).
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-soft"])
    )
    project.all_values()  # does not raise


def test_unresolved_build_dependency_stays_a_plain_string():
    # build_dependencies() itself stays permissive (like soft/hard_dependencies):
    # the TUI's lint/dependency-graph views consume it directly and want to report
    # a broken reference rather than crash on it.
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-build"])
    )
    assert project["wrong-build"].build_dependencies() == ["idonotexist"]


def test_unresolved_build_dependency_raises_at_skaffold_generation():
    # CHProject.all_dependencies() (soft/hard only) never walks build_dependencies -
    # that's a separate resolution against a different namespace (apps, base
    # images, tasks), matching the old get_included_applications/get_included_builds
    # split. But skaffold generation still validates and raises for an unresolved
    # *explicit* build dependency, matching the old validate_dependencies' check -
    # unlike an unresolved *guessed* (Dockerfile-derived) one, which stays permissive.
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-build"])
    )
    with pytest.raises(DependencyUnknownError):
        project.skaffold.generate(write_on_disk=False)


# Three-level chains (base < mid < top, mirroring cloud-harness < mnp < ifn) -
# the case the old cloudharness_path-only model couldn't represent at all.


def _write_app(root, name, *, values=None, dockerfile="FROM scratch\n", tasks=()):
    app_dir = root / "applications" / name
    if dockerfile is not None:
        (app_dir).mkdir(parents=True, exist_ok=True)
        (app_dir / "Dockerfile").write_text(dockerfile)
    if values is not None:
        (app_dir / "deploy").mkdir(parents=True, exist_ok=True)
        (app_dir / "deploy" / "values.yaml").write_text(values)
    for task_name, task_dockerfile in tasks:
        task_dir = app_dir / "tasks" / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "Dockerfile").write_text(task_dockerfile)
    return app_dir


def three_layer_project(tmp_path, **config_kwargs):
    base, mid, top = tmp_path / "base", tmp_path / "mid", tmp_path / "top"
    for root, name in ((base, "baseproj"), (mid, "midproj"), (top, "topproj")):
        (root / "deployment-configuration").mkdir(parents=True)
        (root / "deployment-configuration" / "values-template.yaml").write_text(
            f"name: {name}\n"
        )

    (base / "deployment-configuration" / "value-template.yaml").write_text(
        "harness:\n  from_base: true\n"
    )
    (top / "deployment-configuration" / "value-template.yaml").write_text(
        "harness:\n  from_top: true\n"
    )

    # onlybase: exists only at the bottom - a pure pass-through app from top's
    # perspective.
    _write_app(base, "onlybase", values="harness:\n  layer: base\n")
    # onlymid: exists only at the middle layer.
    _write_app(mid, "onlymid", values="harness:\n  layer: mid\n")
    # overridden: declared at all three layers, Dockerfile only at the base -
    # covers dockerfile fallback and all_values()/app_defaults precedence
    # through the full chain at once. Its task is also only declared at the
    # base, to check _scan_tasks() recursion through two overriding layers.
    _write_app(
        base,
        "overridden",
        values="harness:\n  layer: base\n",
        tasks=[("onlytask", "FROM scratch\n")],
    )
    _write_app(mid, "overridden", values="harness:\n  layer: mid\n", dockerfile=None)
    _write_app(top, "overridden", values="harness:\n  layer: top\n", dockerfile=None)

    for root, images in (
        (base, ["onlybase-img", "shared-img"]),
        (mid, ["onlymid-img"]),
        (top, ["shared-img"]),
    ):
        for image_name in images:
            image_dir = root / "infrastructure" / "base-images" / image_name
            image_dir.mkdir(parents=True)
            (image_dir / "Dockerfile").write_text("FROM scratch\n")

    return chain(base, mid, top, config=CHDeployConfig(**config_kwargs))


def test_three_level_app_only_in_base_resolves_from_top(tmp_path):
    project = three_layer_project(tmp_path)
    app = project["onlybase"]

    # Pass-through: the layer that actually scanned it is the base, but the
    # project it's being built for is the top - these must differ.
    assert app.containing_project is project.base.base
    assert app.project is project

    assert app.all_values()["harness"]["layer"] == "base"
    # app_defaults recurse the *whole* chain regardless of which layer a
    # pass-through app was scanned at: both the base's and the top's own
    # value-template.yaml contribute. Using .containing_project here instead
    # of .project would only ever walk downward from the base, never
    # reaching the top's value-template.yaml at all - the actual regression
    # the .project/.containing_project split fixes.
    assert app.all_values()["harness"]["from_top"] is True
    assert app.all_values()["harness"]["from_base"] is True
    assert app.image_name == "topproj/onlybase"


def test_three_level_app_only_in_mid_resolves_from_top(tmp_path):
    project = three_layer_project(tmp_path)
    app = project["onlymid"]

    assert app.containing_project is project.base
    assert app.project is project
    assert app.all_values()["harness"]["layer"] == "mid"
    assert app.image_name == "topproj/onlymid"


def test_three_level_app_overridden_at_every_layer_merges_through_full_chain(
    tmp_path,
):
    project = three_layer_project(tmp_path)
    app = project["overridden"]

    # Top's own values win on the shared "layer" key...
    assert app.all_values()["harness"]["layer"] == "top"
    # ...but the Dockerfile only exists at the base, and must still resolve
    # two hops up through mid's and top's own Dockerfile-less overrides.
    assert app.dockerfile.exists()
    assert app.dockerfile.path == project.base.base["overridden"].path / "Dockerfile"
    assert app.image_name == "topproj/overridden"


def test_three_level_base_images_compose_across_all_levels(tmp_path):
    project = three_layer_project(tmp_path)

    assert set(project.base_images) == {"onlybase-img", "onlymid-img", "shared-img"}
    # shared-img exists at both the base and the top - top's own wins, and is
    # a distinct instance/path from the base's.
    top_shared = project.base_images["shared-img"]
    base_shared = project.base.base.base_images["shared-img"]
    assert top_shared.path != base_shared.path
    assert top_shared.path.is_relative_to(tmp_path / "top")


def test_three_level_bottom_only_task_survives_two_overriding_layers(tmp_path):
    project = three_layer_project(tmp_path)
    app = project["overridden"]

    # Sanity-check the fixture: the task really is only declared at the base.
    assert "overridden-onlytask" in project.base.base["overridden"].tasks
    # "overridden" has no tasks of its own at mid or top - only at the base,
    # two layers down from where app.tasks is actually being read.
    task = app.tasks["overridden-onlytask"]
    assert task.dockerfile.exists()
    assert task.path == project.base.base["overridden"].path / "tasks" / "onlytask"


def test_three_level_dependency_resolves_to_top_level_instance(tmp_path):
    # onlybase is a pass-through app (base-only); a dependency on "overridden"
    # (overridden at every layer) must resolve to the *top*-level instance -
    # not the stale base-only one - matching how soft/hard_dependencies now
    # resolve via .project (the top), not .containing_project.
    base = tmp_path / "base"
    _write_app(
        base,
        "depender",
        values="harness:\n  dependencies:\n    hard: [overridden]\n",
    )
    project = three_layer_project(tmp_path)
    depender = project["depender"]

    assert depender.containing_project is project.base.base
    [dep] = depender.hard_dependencies
    assert dep is project["overridden"]
    assert dep is not project.base.base["overridden"]


def test_app_test_fragment_reads_own_values(resources_project):
    # myapp's own values.yaml declares unit test commands directly.
    unit = resources_project["myapp"].test.unit
    assert unit.enabled is True
    assert unit.commands == ["tox", 'echo "hello"']


def test_app_test_fragment_falls_back_to_defaults(resources_project):
    # accounts declares no test config of its own - everything comes from
    # deployment-configuration/value-template.yaml's app defaults.
    test = resources_project["accounts"].test
    assert test.unit.enabled is True
    assert test.unit.commands == []
    assert test.api.enabled is False
    assert test.api.checks == ["all"]
    assert test.e2e.enabled is False
    assert test.e2e.smoketest is True


def test_app_test_fragment_commands_empty_when_unit_tests_disabled(tmp_path):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    (app_dir / "deploy").mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "deploy" / "values.yaml").write_text(
        "harness:\n  test:\n    unit:\n      enabled: false\n"
        "      commands: ['pytest tests/']\n"
    )
    project = chain(root, root, config=CHDeployConfig())
    assert project["myapp"].test.unit.commands == []


def test_app_openapi_reads_server_urls_from_real_spec():
    # samples' real api/openapi.yaml declares servers: [{url: /api}].
    project = CHProject(CLOUDHARNESS_ROOT, config=CHDeployConfig())
    assert project["samples"].openapi.server_urls == ["/api"]


def test_app_openapi_empty_when_no_spec_file(resources_project):
    # myapp has no api/openapi.yaml at all in this fixture tree.
    openapi = resources_project["myapp"].openapi
    assert openapi.exists() is False
    assert openapi.server_urls == []


def test_app_secrets_reads_real_declaration():
    # samples' real values.yaml declares harness.secrets.asecret = "value".
    project = CHProject(CLOUDHARNESS_ROOT, config=CHDeployConfig())
    assert project["samples"].secrets == {"asecret": "value"}


def test_app_secrets_empty_when_not_declared(resources_project):
    assert resources_project["myapp"].secrets == {}


def test_app_database_reads_own_values(resources_project):
    # myapp's own values.yaml declares harness.database.connect_string: "".
    assert resources_project["myapp"].database.get("connect_string") == ""


def test_app_database_connect_string_unset_when_not_declared():
    # events gets the app-defaults' own database block (connect_string:
    # None), not an empty-string sentinel - it never opted into one.
    project = CHProject(CLOUDHARNESS_ROOT, config=CHDeployConfig())
    assert project["events"].database.get("connect_string") is None
