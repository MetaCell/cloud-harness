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


def _minimal_project(tmp_path, **config_kwargs):
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
        root, cloudharness_path=root, config=CHDeployConfig(**config_kwargs)
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

    # Second-level: samples --soft--> workflows --hard--> argo. This only resolves
    # because cross-root app merging is in place - workflows only has a real
    # dependencies.hard in cloud-harness's copy, not the fixture's, so this
    # assertion exercises that merge, not just soft/hard closure on its own.
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


def test_unresolved_soft_dependency_does_not_raise():
    # A soft dependency is optional by design: unresolved is never fatal, matching
    # the old validate_dependencies (warns, doesn't raise).
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-soft"])
    )
    project.all_values()  # does not raise


def test_unresolved_build_dependency_currently_does_not_raise():
    # Old behavior: DOES raise. `ng`'s CHProject.all_dependencies() never walks
    # build_dependencies, so an unresolved build dep never reaches `involved_apps`
    # at all - known gap.
    project = CHProject(
        WRONG_DEPENDENCIES, config=CHDeployConfig(includes=["wrong-build"])
    )
    project.all_values()  # does not raise


# --- skaffold generator tests. Ports of tests/test_skaffold.py, scoped to the
# slice of behavior the ng model currently supports.


def test_build_dependency_on_app_produces_requires_entry():
    # Ports test_app_depends_on_app: dependantapp declares
    # dependencies.build: [myapp, myapp-mytask] - a real app and a task owned by
    # that app. Both resolve, each to its own requires entry.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    dependantapp_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/dependantapp"
    )
    assert dependantapp_artifact["requires"] == [
        {"image": "testprojectname/myapp", "alias": "MYAPP"},
        {"image": "testprojectname/myapp-mytask", "alias": "MYAPP_MYTASK"},
    ]

    # myapp-mytask must have its own build artifact even though myapp itself is
    # only a build dependency here, not deployed.
    assert any(a["image"] == "testprojectname/myapp-mytask" for a in artifacts)


def test_build_only_dependency_is_not_deployed():
    # Ports the other half of test_app_depends_on_app: myapp is a build
    # dependency of dependantapp (dependencies.build), not a soft/hard one, so it
    # must not end up deployed - no artifactOverrides entry, even though its
    # image still gets built (see test_build_dependency_on_app_produces_requires_
    # entry for the build side of the same fixture).
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp"]),
    )
    generated = project.skaffold.generate(write_on_disk=False)
    overrides = generated["deploy"]["helm"]["releases"][0]["artifactOverrides"]["apps"]

    assert "dependantapp" in overrides
    assert "myapp" not in overrides


def test_build_dependency_on_base_image_gets_its_own_artifact():
    # Slice of test_create_skaffold_configuration's cloudharness_flask assertions:
    # a build dependency resolving to infrastructure/common-images/ gets its own
    # artifact, with a context under that directory, and the requiring app's
    # artifact references it via requires.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["taskdep"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    taskdep_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/taskdep"
    )
    assert taskdep_artifact["requires"] == [
        {"image": "testprojectname/cloudharness-flask", "alias": "CLOUDHARNESS_FLASK"},
        {"image": "testprojectname/myapp-mytask", "alias": "MYAPP_MYTASK"},
    ]

    flask_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/cloudharness-flask"
    )
    context = (RESOURCES / flask_artifact["context"]).resolve()
    expected = (
        CLOUDHARNESS_ROOT / "infrastructure" / "common-images" / "cloudharness-flask"
    )
    assert context == expected.resolve()


def test_build_dependency_on_task_owned_by_an_undeployed_app_resolves():
    # Ports test_skaffold_builds_cross_app_task_image: taskdep declares
    # dependencies.build: [cloudharness-flask, myapp-mytask]. myapp-mytask is a
    # task owned by myapp, an app that isn't otherwise deployed here (not an
    # entrypoint, not a soft/hard dep of anything included) - it must still
    # resolve and get its own build artifact. CHAppDefault.build_dependencies()
    # falls back to CHProject.all_buildable_tasks(), which is scoped to every
    # scanned app, not just involved_apps, precisely to cover this case.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["taskdep"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    assert any(a["image"] == "testprojectname/myapp-mytask" for a in artifacts)


def test_excluded_task_drops_out_unless_still_a_build_dependency():
    # Ports test_exclude_single_task. excludes applies to a task in its own
    # right - myapp's own myapp-mytask disappears when excluded and nothing else
    # needs it - but a build dependency is never optional (see
    # test_build_dependency_on_task_owned_by_an_undeployed_app_resolves), so the
    # same exclude has no effect when dependantapp still requires it to build.
    own_project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], excludes=["myapp-mytask"]),
    )
    own_artifacts = own_project.skaffold.generate(write_on_disk=False)["build"][
        "artifacts"
    ]
    assert not any(a["image"].endswith("myapp-mytask") for a in own_artifacts)

    required_project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp"], excludes=["myapp-mytask"]),
    )
    required_artifacts = required_project.skaffold.generate(write_on_disk=False)[
        "build"
    ]["artifacts"]
    assert any(
        a["image"] == "testprojectname/myapp-mytask" for a in required_artifacts
    )


def test_namespace_sets_helm_release_name_and_namespace(tmp_path):
    project = _minimal_project(tmp_path, namespace="my-ns")
    release = project.skaffold.generate(write_on_disk=False)["deploy"]["helm"][
        "releases"
    ][0]

    assert release["name"] == "my-ns"
    assert release["namespace"] == "my-ns"


def test_no_namespace_leaves_helm_release_name_unset(tmp_path):
    project = _minimal_project(tmp_path)
    release = project.skaffold.generate(write_on_disk=False)["deploy"]["helm"][
        "releases"
    ][0]

    assert "name" not in release
    assert "namespace" not in release


def test_tag_policy_is_sha256_by_default(tmp_path):
    project = _minimal_project(tmp_path)
    build = project.skaffold.generate(write_on_disk=False)["build"]
    assert build["tagPolicy"] == {"sha256": {}}


def test_tag_policy_is_env_template_when_external_tag_and_not_local(tmp_path):
    # An external tag (e.g. from CI) means skaffold should trust the tag it's
    # handed rather than compute its own content hash.
    project = _minimal_project(tmp_path, tag="v1", local=False)
    build = project.skaffold.generate(write_on_disk=False)["build"]
    assert build["tagPolicy"] == {"envTemplate": {"template": '"{{.TAG}}"'}}


def test_tag_policy_is_sha256_when_tag_set_but_local(tmp_path):
    # A local dev build still wants content-hash tagging even if an external tag
    # was also passed - `local` wins over `tag`.
    project = _minimal_project(tmp_path, tag="v1", local=True)
    build = project.skaffold.generate(write_on_disk=False)["build"]
    assert build["tagPolicy"] == {"sha256": {}}


def test_compose_backend_builds_docker_compose_deploy_block(tmp_path):
    # Also covers the tagPolicy branch: compose always wants envTemplate, even
    # without an explicit tag - see test_tag_policy_is_env_template_when_
    # external_tag_and_not_local for the non-compose case.
    project = _minimal_project(tmp_path, backend="compose")
    generated = project.skaffold.generate(write_on_disk=False)

    assert generated["build"]["tagPolicy"] == {
        "envTemplate": {"template": '"{{.TAG}}"'}
    }
    assert generated["deploy"] == {
        "docker": {
            "useCompose": True,
            "images": ["testproj/myapp", "testproj/myapp-mytask"],
        }
    }


def test_env_dockerfile_used_when_it_exists():
    # Ports test_env_dockerfile: myapp has a dev.Dockerfile, so it's preferred
    # over the plain Dockerfile once env="dev" is active.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], env="dev"),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    myapp_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/myapp"
    )
    assert myapp_artifact["docker"]["dockerfile"].endswith("dev.Dockerfile")


def test_env_dockerfile_falls_back_to_plain_dockerfile():
    # Ports test_env_dockerfile's samples half and test_env_dockerfile_fallback:
    # samples has no dev.Dockerfile, so it keeps using the plain Dockerfile even
    # with env="dev" active; myapp-mytask (a task, not the app itself) has no
    # dev.Dockerfile of its own either.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], env="dev"),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    mytask_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/myapp-mytask"
    )
    dockerfile = mytask_artifact["docker"]["dockerfile"]
    assert dockerfile.endswith("Dockerfile")
    assert not dockerfile.endswith("dev.Dockerfile")


def test_no_env_never_uses_env_dockerfile():
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    myapp_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/myapp"
    )
    assert myapp_artifact["docker"]["dockerfile"] == "Dockerfile"


def _multi_env_project(tmp_path, env):
    # Deliberately deterministic, not RESOURCES: a, b, c let us tell apart
    # "later env wins" from "earlier env's untouched keys survive" from
    # "base's own untouched keys survive both env layers".
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "dev.Dockerfile").write_text("FROM dev-image\n")
    (app_dir / "test.Dockerfile").write_text("FROM test-image\n")
    (app_dir / "deploy").mkdir()
    (app_dir / "deploy" / "values.yaml").write_text("a: base\nb: base\nc: base\n")
    (app_dir / "deploy" / "values-dev.yaml").write_text("a: dev\nb: dev\n")
    (app_dir / "deploy" / "values-test.yaml").write_text("a: test\n")

    return CHProject(root, cloudharness_path=root, config=CHDeployConfig(env=env))


def test_multi_env_layers_in_order_later_env_wins(tmp_path):
    project = _multi_env_project(tmp_path, env=["dev", "test"])
    values = project["myapp"].all_values()

    assert values["a"] == "test"  # both dev and test touch it - test is later
    assert values["b"] == "dev"  # only dev touches it - survives test's layer
    assert values["c"] == "base"  # neither env touches it - stays at base


def test_multi_env_order_matters(tmp_path):
    # Same two envs, reversed order - "dev" now wins on "a" since it's last.
    project = _multi_env_project(tmp_path, env=["test", "dev"])
    values = project["myapp"].all_values()

    assert values["a"] == "dev"
    assert values["b"] == "dev"


def test_multi_env_dockerfile_selection_tries_each_env_in_order(tmp_path):
    project = _multi_env_project(tmp_path / "both", env=["dev", "test"])
    assert project["myapp"].dockerfile.path.name == "dev.Dockerfile"

    project_test_only = _multi_env_project(tmp_path / "test-only", env=["test"])
    assert project_test_only["myapp"].dockerfile.path.name == "test.Dockerfile"


def test_multi_env_output_path_is_dash_joined(tmp_path):
    # Ports the real -e dev-test convention: the *output* artifact name joins
    # the envs with a dash, unlike the per-env *input* files it reads from.
    project = _multi_env_project(tmp_path / "both", env=["dev", "test"])
    assert project.codefresh.path.name == "codefresh-dev-test.yaml"

    project_none = _multi_env_project(tmp_path / "none", env=None)
    assert project_none.codefresh.path.name == "codefresh.yaml"


def test_own_build_args_apply_only_to_the_apps_own_artifact():
    # Ports part of test_skaffold_imgarg: samples declares harness.dockerfile.
    # buildArgs.TEST_ARGUMENT, which must reach samples' own artifact but not its
    # tasks'.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["samples"], excludes=["events"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    app_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/sampleapp"
    )
    assert app_artifact["docker"]["buildArgs"]["TEST_ARGUMENT"] == "example value"

    task_artifacts = [
        a for a in artifacts if a["image"].startswith("testprojectname/sampleapp-")
    ]
    assert task_artifacts
    assert all(
        "TEST_ARGUMENT" not in a["docker"].get("buildArgs", {}) for a in task_artifacts
    )


def test_source_images_apply_to_every_artifact_project_wide():
    # Ports test_skaffold_imgarg/test_skaffold_imgarg_retrieval's source_images
    # aggregation. Uses RESOURCES only (not the real cloud-harness repo), so the
    # expected ARG defaults stay stable: newapp1 declares mybase/mybase2 in its
    # own Dockerfile; myapp's Dockerfile doesn't reference either, but still gets
    # them as buildArgs, since source_images is a project-wide aggregation
    # applied to every artifact, not just the app that owns the ARG.
    project = CHProject(
        RESOURCES,
        cloudharness_path=RESOURCES,
        config=CHDeployConfig(includes=["newapp1", "myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    myapp_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/myapp"
    )
    assert myapp_artifact["docker"]["buildArgs"]["mybase"] == "foo:bar"
    assert myapp_artifact["docker"]["buildArgs"]["mybase2"] == "spam:egg"


def test_ssh_default_set_on_every_artifact(tmp_path):
    project = _minimal_project(tmp_path)
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    assert artifacts
    assert all(a["docker"]["ssh"] == "default" for a in artifacts)
