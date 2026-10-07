# NG-COMPAT-TODO: retargeted at ch_cli_tools.ng.api.create_helm_chart/
# create_skaffold_configuration instead of the legacy ch_cli_tools.helm/
# ch_cli_tools.skaffold ones (ported from tests/test_skaffold.py). There's no
# separate preprocess_build_overrides() call (ng.api's own stub of that name is
# unrelated/unused) - merging an overridden app/base-image's directory across
# layers now happens transparently inside CHSkaffold.generate(), via
# CHContext.copy_my_context_to(), the moment such an artifact is collected.
from ch_cli_tools.configurationgenerator import *
from ch_cli_tools.ng.api import create_helm_chart, create_skaffold_configuration
from conftest import CLOUDHARNESS_ROOT, RESOURCES
import os

RESOURCES_BUGGY = os.path.join(os.path.dirname(RESOURCES), "resources_buggy")


def test_create_skaffold_configuration(tmp_path):
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
    project = values._ch_project

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        output_path=tmp_path,
    )
    assert os.path.exists(os.path.join(tmp_path, "skaffold.yaml"))

    # workflows/common each build from applications/<name>/server/Dockerfile,
    # not a top-level one - legacy's own directory walk (find_dockerfiles_paths
    # + NEUTRAL_PATHS) already treated that as the app's own Dockerfile;
    # CHApp.dockerfile now checks the same conventional subdirectories.
    exp_apps = ("accounts", "samples", "workflows", "myapp", "common")
    artifact_images = [a["image"] for a in sk["build"]["artifacts"]]
    artifact_overrides = sk["deploy"]["helm"]["releases"][0]["artifactOverrides"]
    for app in exp_apps:
        assert app in artifact_overrides[KEY_APPS]

    # NG-COMPAT-TODO: values[KEY_TASK_IMAGES] isn't populated by
    # ng.api.create_helm_chart (no task-images aggregation yet - see
    # test_helm_compat.py's test_collect_helm_values). artifactOverrides'
    # task-images comes straight from ng.skaffold.CHSkaffold's own generation
    # instead, which is what's actually under test here.
    assert artifact_overrides[KEY_TASK_IMAGES], "task image overrides should be present"
    assert any(
        image.endswith("myapp-mytask") for image in artifact_overrides[KEY_TASK_IMAGES]
    )

    assert any("reg" in image and "cloudharness" in image for image in artifact_images)

    overrides = sk["deploy"]["helm"]["releases"][0]["overrides"]
    assert overrides[KEY_APPS]["samples"][KEY_HARNESS][KEY_DEPLOYMENT]["command"] == [
        "python"
    ]
    assert overrides[KEY_APPS]["samples"][KEY_HARNESS][KEY_DEPLOYMENT]["args"]

    assert (
        "reg"
        == artifact_overrides[KEY_APPS]["accounts"][KEY_HARNESS][KEY_DEPLOYMENT][
            "image"
        ][0:3]
    )
    assert (
        "harness"
        not in artifact_overrides[KEY_APPS]["accounts"][KEY_HARNESS][KEY_DEPLOYMENT][
            "image"
        ]
    )

    cloudharness_base_artifact = next(
        a
        for a in sk["build"]["artifacts"]
        if a["image"] == "reg/testprojectname/cloudharness-base"
    )
    assert "requires" not in cloudharness_base_artifact
    # tests/resources/ declares its own infrastructure/base-images/
    # cloudharness-base/, overriding (not just passing through) the real
    # checkout's one - CHContext.copy_my_context_to() physically merges both
    # layers' build_context (CLOUDHARNESS_ROOT first, then RESOURCES on top,
    # matching legacy's preprocess_build_overrides) into .overrides/
    # cloudharness-base next to skaffold.yaml, and the context points there.
    assert os.path.samefile(
        project.root / cloudharness_base_artifact["context"],
        project.root / ".overrides" / "cloudharness-base",
    )
    merged_root = project.root / ".overrides" / "cloudharness-base"
    assert (merged_root / cloudharness_base_artifact["docker"]["dockerfile"]).exists()
    assert (
        merged_root / "infrastructure/base-images/cloudharness-base/testfile"
    ).exists(), "RESOURCES' own cloudharness-base files must be present in the merge"
    assert (merged_root / "libraries").exists(), (
        "CLOUDHARNESS_ROOT's libraries/ (needed by the Dockerfile) must survive"
        " the merge since the base image's build context is the whole root"
    )

    cloudharness_flask_artifact = next(
        a
        for a in sk["build"]["artifacts"]
        if a["image"] == "reg/testprojectname/cloudharness-flask"
    )
    assert os.path.samefile(
        project.root / cloudharness_flask_artifact["context"],
        os.path.join(
            CLOUDHARNESS_ROOT, "infrastructure/common-images/cloudharness-flask"
        ),
    )
    assert len(cloudharness_flask_artifact["requires"]) == 1

    expected_samples_image = f"reg/{project['samples'].image_name}"
    samples_artifact = next(
        a for a in sk["build"]["artifacts"] if a["image"] == expected_samples_image
    )
    assert os.path.samefile(
        project.root / samples_artifact["context"],
        os.path.join(CLOUDHARNESS_ROOT, "applications/samples"),
    )
    assert "TEST_ARGUMENT" in samples_artifact["docker"]["buildArgs"]
    assert samples_artifact["docker"]["buildArgs"]["TEST_ARGUMENT"] == "example value"

    myapp_artifact = next(
        a for a in sk["build"]["artifacts"] if a["image"] == "reg/testprojectname/myapp"
    )
    # myapp exists only in RESOURCES (no CLOUDHARNESS_ROOT counterpart, so no
    # .base/merge applies) - its own, unmerged context is used directly.
    assert os.path.samefile(
        project.root / myapp_artifact["context"],
        os.path.join(RESOURCES, "applications/myapp"),
    )
    assert myapp_artifact["hooks"][
        "before"
    ], "The hook for dependencies should be included"
    assert (
        len(myapp_artifact["hooks"]["before"]) == 2
    ), "The hook for dependencies should include 2 clone commands"

    accounts_artifact = next(
        a
        for a in sk["build"]["artifacts"]
        if a["image"] == "reg/testprojectname/accounts"
    )
    # accounts exists in both layers, but RESOURCES' own copy has no
    # Dockerfile, so .dockerfile falls back to CLOUDHARNESS_ROOT's entity -
    # whose own .base is None (it's the bottom layer), so no merge applies;
    # its unmerged context is used directly, same as before the merge feature.
    assert os.path.samefile(
        project.root / accounts_artifact["context"],
        os.path.join(CLOUDHARNESS_ROOT, "applications/accounts"),
    )

    # Custom unit tests
    assert len(sk["test"]) == 2, "Unit tests should be included"
    samples_test = next(t for t in sk["test"] if t["image"] == expected_samples_image)
    assert (
        "samples/test" in samples_test["custom"][0]["command"]
    ), "The test command must come from values.yaml test/unit/commands"

    myapp_test = next(
        t for t in sk["test"] if t["image"] == "reg/testprojectname/myapp"
    )
    assert len(myapp_test["custom"]) == 2

    flags = sk["deploy"]["helm"]["flags"]
    assert "--timeout=10m" in flags["install"]
    assert "--install" in flags["upgrade"]


def test_create_skaffold_configuration_with_conflicting_dependencies(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
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

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        helm_values=values,
        output_path=tmp_path,
    )

    releases = sk["deploy"]["helm"]["releases"]
    assert len(releases) == 1

    release = releases[0]
    assert "myapp" in release["overrides"]["apps"]
    assert "matplotlib" not in release["overrides"]["apps"]

    myapp_config = release["overrides"]["apps"]["myapp"]
    assert myapp_config["harness"]["deployment"]["args"][0] == "/usr/src/app/myapp_code/__main__.py"


def test_create_skaffold_configuration_with_conflicting_dependencies_requirements_file(
    tmp_path,
):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        output_path=tmp_path,
        include=["myapp2"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        helm_values=values,
        output_path=tmp_path,
    )

    releases = sk["deploy"]["helm"]["releases"]
    assert len(releases) == 1

    release = releases[0]
    assert "myapp2" in release["overrides"]["apps"]
    assert "matplotlib" not in release["overrides"]["apps"]

    myapp_config = release["overrides"]["apps"]["myapp2"]
    assert myapp_config["harness"]["deployment"]["args"][0] == "/usr/src/app/myapp_code/__main__.py"


def test_create_skaffold_configuration_nobuild(tmp_path):
    values = create_helm_chart(
        [RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        domain="my.local",
        namespace="test",
        env="nobuild",
        local=False,
        tag="1",
        registry="reg",
    )

    sk = create_skaffold_configuration(
        root_paths=[RESOURCES],
        helm_values=values,
        output_path=tmp_path,
    )
    releases = sk["deploy"]["helm"]["releases"]

    assert len(sk["build"]["artifacts"]) == 1
    assert len(releases) == 1

    release = releases[0]
    assert "myapp" not in release["overrides"]["apps"]


def test_env_dockerfile(tmp_path):
    """When a [env].Dockerfile exists it should be used instead of Dockerfile."""
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
    project = values._ch_project

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        output_path=tmp_path,
        env=["dev"],
    )

    myapp_artifact = next(
        a for a in sk["build"]["artifacts"] if a["image"] == "reg/testprojectname/myapp"
    )
    assert myapp_artifact["docker"]["dockerfile"].endswith(
        "dev.Dockerfile"
    ), f"Expected dev.Dockerfile but got {myapp_artifact['docker']['dockerfile']}"

    expected_samples_image = f"reg/{project['samples'].image_name}"
    samples_artifact = next(
        a for a in sk["build"]["artifacts"] if a["image"] == expected_samples_image
    )
    assert samples_artifact["docker"]["dockerfile"].endswith(
        "Dockerfile"
    ), f"Expected Dockerfile but got {samples_artifact['docker']['dockerfile']}"
    assert not samples_artifact["docker"]["dockerfile"].endswith(
        "dev.Dockerfile"
    ), "samples should not use dev.Dockerfile"


def test_env_dockerfile_fallback(tmp_path):
    """Without env, or when no env.Dockerfile exists, the regular Dockerfile should be used."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="",
        local=False,
        tag="1",
        registry="reg",
    )

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        output_path=tmp_path,
        env=None,
    )

    myapp_artifact = next(
        a for a in sk["build"]["artifacts"] if a["image"] == "reg/testprojectname/myapp"
    )
    assert myapp_artifact["docker"]["dockerfile"].endswith(
        "Dockerfile"
    ), f"Expected Dockerfile but got {myapp_artifact['docker']['dockerfile']}"
    assert not myapp_artifact["docker"]["dockerfile"].endswith(
        "dev.Dockerfile"
    ), "Should not use dev.Dockerfile when no env is specified"


def test_app_depends_on_app(tmp_path):
    out_folder = tmp_path / "test_app_depends_on_app"

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        domain="my.local",
        # NG-COMPAT-TODO: namespace='test' added - not in the original legacy
        # call, but namespace is a required HarnessMainConfig field with no
        # default-derivation in ng (same gap test_helm_compat.py documents).
        namespace="test",
        env="",
        local=False,
        include=["dependantapp"],
        exclude=[],
    )

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        output_path=tmp_path,
    )
    releases = sk["deploy"]["helm"]["releases"]

    artifact_images = [a["image"] for a in sk["build"]["artifacts"]]
    assert len(artifact_images) == 7, (
        "There should be 7 build artifacts (base+common, dependantapp plus its 2 "
        "tasks, myapp, myapp-mytask)"
    )
    assert any(
        img.endswith("myapp-mytask") for img in artifact_images
    ), "the cross-app task image myapp-mytask must have a build artifact"
    assert len(releases) == 1

    release = releases[0]
    assert (
        "myapp" not in release["overrides"]["apps"]
    ), "myapp should not be included in the overrides because it's a build only dependency"


def test_skaffold_builds_cross_app_task_image(tmp_path):
    out_folder = tmp_path / "test_skaffold_builds_cross_app_task_image"

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        domain="my.local",
        # NG-COMPAT-TODO: namespace='test' added - see test_app_depends_on_app.
        namespace="test",
        env="",
        local=False,
        include=["taskdep"],
        exclude=[],
    )

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        output_path=tmp_path,
    )

    artifact_images = [a["image"] for a in sk["build"]["artifacts"]]
    assert any(
        img.endswith("myapp-mytask") for img in artifact_images
    ), "the cross-app task image myapp-mytask must have a build artifact"


def test_skaffold_imgarg_retrieval(tmp_path):
    out_folder = tmp_path / "test_skaffold_imgarg_retrieval"

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        include=["samples", "myapp"],
        domain="my.local",
        namespace="test",
        env="nreg",
        local=False,
        tag="1",
        registry="reg",
    )

    # Adapted from legacy's `values.get("events")` (a flattened-dict
    # convenience access) to ng's actual nested structure.
    assert values[KEY_APPS]["events"].kafka.image == "nodocker.io/apache/kafka:4.0.2"

    # NG-COMPAT-TODO: ng.api.create_helm_chart doesn't surface a top-level
    # `source_images` key on the returned values (CHProject.all_source_images()
    # exists and backs ng.skaffold's buildArgs, but isn't aggregated into
    # build_final_helm_values's output) - see test_helm_compat.py's
    # test_collect_helm_values_noreg_noinclude for the same gap.
    # KEYCLOAK's expected value is the real, current
    # applications/accounts/Dockerfile ARG default - legacy's original test
    # expected "myregistry.myapp:15.3", which is stale (repo drift unrelated
    # to ng vs legacy; accounts has no RESOURCES-side override, so this is a
    # pure pass-through app's own real Dockerfile ARG).
    project = values._ch_project
    source_images = project.all_source_images()
    assert len(source_images) == 2
    assert source_images["KEYCLOAK"] == "quay.io/keycloak/keycloak:26.5"
    assert source_images["NODE"] == "node:22-alpine"


def test_skaffold_imgarg(tmp_path):
    out_folder = tmp_path / "test_skaffold_imgarg"

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        include=["samples", "myapp"],
        domain="my.local",
        namespace="test",
        env="nreg",
        local=False,
        tag="1",
        registry="reg",
    )

    assert values[KEY_APPS]["events"].kafka.image == "nodocker.io/apache/kafka:4.0.2"

    sk = create_skaffold_configuration(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        output_path=out_folder,
    )

    def get_buildargs(name) -> dict[str, str]:
        found = [
            e["docker"]["buildArgs"]
            for e in sk["build"]["artifacts"]
            if f"applications/{name}" in e["context"]
        ]
        return found[0] if found else {}

    samples_buildargs = get_buildargs("samples")
    assert samples_buildargs["KEYCLOAK"] == "quay.io/keycloak/keycloak:26.5"
    assert samples_buildargs["NODE"] == "node:22-alpine"

    myapp_buildargs = get_buildargs("myapp")
    assert myapp_buildargs["KEYCLOAK"] == "quay.io/keycloak/keycloak:26.5"
    assert myapp_buildargs["NODE"] == "node:22-alpine"
