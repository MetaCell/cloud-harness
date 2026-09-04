import os
import shutil

from ch_cli_tools.helm import *
from ch_cli_tools.preprocessing import preprocess_build_overrides
from ch_cli_tools.skaffold import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
RESOURCES_BUGGY = os.path.join(HERE, 'resources_buggy')

CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CLOUDHARNESS_DIRNAME = os.path.basename(CLOUDHARNESS_ROOT)


def test_create_skaffold_configuration(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=['samples', 'myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )
    BUILD_DIR = "/tmp/build"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path
    )
    assert os.path.exists(os.path.join(tmp_path, 'skaffold.yaml'))
    # values-overrides.yaml is a reference for discovering image paths, not applied automatically
    assert 'valuesFiles' not in sk['deploy']['helm']['releases'][0]
    exp_apps = ('accounts', 'samples', 'workflows', 'myapp', 'common')
    assert len(sk['build']['artifacts']) == len(
        exp_apps) + len(values[KEY_TASK_IMAGES])
    assert 'reg' in sk['build']['artifacts'][0]['image']
    assert 'cloudharness' in sk['build']['artifacts'][0]['image']
    artifact_overrides = sk['deploy']['helm']['releases'][0]['artifactOverrides']
    for app in exp_apps:
        assert app in artifact_overrides[KEY_APPS]
    for img in values[KEY_TASK_IMAGES]:
        assert img in artifact_overrides[KEY_TASK_IMAGES]

    assert f'reg/testprojectname/cloudharness-base' in (
        a['image'] for a in sk['build']['artifacts'])

    overrides = sk['deploy']['helm']['releases'][0]['overrides']
    assert overrides[KEY_APPS]['samples'][KEY_HARNESS][KEY_DEPLOYMENT]['command'] == [
        'python']
    assert overrides[KEY_APPS]['samples'][KEY_HARNESS][KEY_DEPLOYMENT]['args']

    assert 'reg' == artifact_overrides[KEY_APPS]['accounts'][KEY_HARNESS][KEY_DEPLOYMENT]['image'][0:3]
    assert 'harness' not in artifact_overrides[KEY_APPS]['accounts'][KEY_HARNESS][KEY_DEPLOYMENT]['image']

    cloudharness_base_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == f'reg/testprojectname/cloudharness-base')
    assert cloudharness_base_artifact['context'] == BUILD_DIR
    assert 'requires' not in cloudharness_base_artifact

    cloudharness_flask_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == f'reg/testprojectname/cloudharness-flask')

    assert os.path.samefile(cloudharness_flask_artifact['context'],
                            join(CLOUDHARNESS_ROOT, 'infrastructure/common-images/cloudharness-flask')
                            )

    assert len(cloudharness_flask_artifact['requires']) == 1

    expected_samples_image = values[KEY_APPS]['samples'][KEY_HARNESS][KEY_DEPLOYMENT]['image'].split(':')[0]

    samples_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == expected_samples_image
    )
    assert os.path.samefile(samples_artifact['context'], join(CLOUDHARNESS_ROOT, 'applications/samples'))
    assert 'TEST_ARGUMENT' in samples_artifact['docker']['buildArgs']
    assert samples_artifact['docker']['buildArgs']['TEST_ARGUMENT'] == 'example value'

    myapp_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == f'reg/testprojectname/myapp')
    assert os.path.samefile(myapp_artifact['context'], join(
        RESOURCES, 'applications/myapp'))
    assert myapp_artifact['hooks']['before'], 'The hook for dependencies should be included'
    assert len(myapp_artifact['hooks']['before']) == 2, 'The hook for dependencies should include 2 clone commands'
    accounts_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == f'reg/testprojectname/accounts')
    assert os.path.samefile(accounts_artifact['context'], '/tmp/build/applications/accounts')

    # Custom unit tests
    assert len(sk['test']) == 2, 'Unit tests should be included'

    samples_test = sk['test'][0]
    assert samples_test['image'] == expected_samples_image, 'Unit tests for samples should be included'
    assert "samples/test" in samples_test['custom'][0]['command'], "The test command must come from values.yaml test/unit/commands"

    assert len(sk['test'][1]['custom']) == 2

    flags = sk['deploy']['helm']['flags']
    assert '--timeout=10m' in flags['install']
    assert '--install' in flags['upgrade']

    shutil.rmtree(tmp_path)
    shutil.rmtree(BUILD_DIR)


def test_create_skaffold_configuration_with_conflicting_dependencies(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        output_path=tmp_path,
        include=['myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        helm_values=values,
        merge_build_path=str(tmp_path)
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path
    )

    releases = sk['deploy']['helm']['releases']
    assert len(releases) == 1  # Ensure we only found 1 deployment (for myapp)

    release = releases[0]
    assert 'myapp' in release['overrides']['apps']
    assert 'matplotlib' not in release['overrides']['apps']

    myapp_config = release['overrides']['apps']['myapp']
    assert myapp_config['harness']['deployment']['args'][0] == '/usr/src/app/myapp_code/__main__.py'


def test_create_skaffold_configuration_with_conflicting_dependencies_requirements_file(tmp_path):
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        output_path=tmp_path,
        include=['myapp2'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES_BUGGY],
        helm_values=values,
        merge_build_path=str(tmp_path)
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path
    )

    releases = sk['deploy']['helm']['releases']
    assert len(releases) == 1  # Ensure we only found 1 deployment (for myapp)

    release = releases[0]
    assert 'myapp2' in release['overrides']['apps']
    assert 'matplotlib' not in release['overrides']['apps']

    myapp_config = release['overrides']['apps']['myapp2']
    assert myapp_config['harness']['deployment']['args'][0] == '/usr/src/app/myapp_code/__main__.py'


def test_create_skaffold_configuration_nobuild(tmp_path):
    values = create_helm_chart(
        [RESOURCES],
        output_path=tmp_path,
        include=['myapp'],
        domain="my.local",
        namespace='test',
        env='nobuild',
        local=False,
        tag=1,
        registry='reg'
    )

    BUILD_DIR = "/tmp/build"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path
    )
    releases = sk['deploy']['helm']['releases']

    assert len(sk['build']['artifacts']) == 1
    assert len(releases) == 1  # Ensure we only found 1 deployment (for myapp)

    release = releases[0]
    assert 'myapp' not in release['overrides']['apps']


def test_env_dockerfile(tmp_path):
    """When a [env].Dockerfile exists it should be used instead of Dockerfile."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=['samples', 'myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )
    BUILD_DIR = "/tmp/build"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path,
        env=['dev']
    )

    myapp_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == f'reg/testprojectname/myapp')
    # myapp has a dev.Dockerfile so it should be used
    assert myapp_artifact['docker']['dockerfile'].endswith('dev.Dockerfile'), \
        f"Expected dev.Dockerfile but got {myapp_artifact['docker']['dockerfile']}"

    # samples has no dev.Dockerfile, so it should fall back to Dockerfile
    expected_samples_image = values[KEY_APPS]['samples'][KEY_HARNESS][KEY_DEPLOYMENT]['image'].split(':')[0]
    samples_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == expected_samples_image)
    assert samples_artifact['docker']['dockerfile'].endswith('Dockerfile'), \
        f"Expected Dockerfile but got {samples_artifact['docker']['dockerfile']}"
    assert not samples_artifact['docker']['dockerfile'].endswith('dev.Dockerfile'), \
        "samples should not use dev.Dockerfile"

    shutil.rmtree(tmp_path)
    shutil.rmtree(BUILD_DIR)


def test_env_dockerfile_fallback(tmp_path):
    """Without env, or when no env.Dockerfile exists, the regular Dockerfile should be used."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=tmp_path,
        include=['myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='',
        local=False,
        tag=1,
        registry='reg'
    )
    BUILD_DIR = "/tmp/build2"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path,
        env=None
    )

    myapp_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == f'reg/testprojectname/myapp')
    assert myapp_artifact['docker']['dockerfile'].endswith('Dockerfile'), \
        f"Expected Dockerfile but got {myapp_artifact['docker']['dockerfile']}"
    assert not myapp_artifact['docker']['dockerfile'].endswith('dev.Dockerfile'), \
        "Should not use dev.Dockerfile when no env is specified"

    shutil.rmtree(tmp_path)
    shutil.rmtree(BUILD_DIR)


def test_app_depends_on_app(tmp_path):
    out_folder = tmp_path / 'test_app_depends_on_app'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='', local=False, include=["dependantapp"], exclude=[])

    BUILD_DIR = "/tmp/build"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path
    )
    releases = sk['deploy']['helm']['releases']

    artifact_images = [a['image'] for a in sk['build']['artifacts']]
    assert len(artifact_images) == 7, \
        "There should be 7 build artifacts (base+common, dependantapp plus its 2 tasks, myapp, myapp-mytask)"
    # myapp-mytask is a build dependency of dependantapp, so it must be built even though
    # its owner app (myapp) is not deployed.
    assert any(img.endswith('myapp-mytask') for img in artifact_images), \
        "the cross-app task image myapp-mytask must have a build artifact"
    assert len(releases) == 1  # Ensure we only found 1 deployment (for myapp)

    release = releases[0]
    assert 'myapp' not in release['overrides']['apps'], "myapp should not be included in the overrides because it's a build only dependency"


def test_skaffold_builds_cross_app_task_image(tmp_path):
    out_folder = tmp_path / 'test_skaffold_builds_cross_app_task_image'

    # taskdep depends on myapp-mytask (a task image owned by myapp, which is not deployed).
    # Skaffold must still emit a build artifact for the task image.
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='', local=False, include=["taskdep"], exclude=[])

    BUILD_DIR = "/tmp/build_cross_app_task"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths,
        helm_values=values,
        output_path=tmp_path
    )

    artifact_images = [a['image'] for a in sk['build']['artifacts']]
    assert any(img.endswith('myapp-mytask') for img in artifact_images), \
        "the cross-app task image myapp-mytask must have a build artifact"

    shutil.rmtree(tmp_path)
    shutil.rmtree(BUILD_DIR)


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
        tag=1,
        registry="reg",
    )

    assert values.get("events").kafka.image == "nodocker.io/apache/kafka:4.0.2"

    # Ensure in the test that the Helm is well formed
    source_images = values.get("source_images")
    assert len(source_images) == 3
    assert source_images["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert source_images["NODE"] == "node:22-alpine"
    assert get_source_images(values) == {
        "KEYCLOAK": "myregistry.myapp:15.3",
        "NODE": "node:22-alpine",
        # Not a build argument of any Dockerfile: declared by CloudHarness so that the
        # gatekeeper image is configured in a single place
        "GATEKEEPER": "quay.io/gogatekeeper/gatekeeper:4.6.0",
    }


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
        tag=1,
        registry="reg",
    )

    assert values.get("events").kafka.image == "nodocker.io/apache/kafka:4.0.2"

    BUILD_DIR = "/tmp/build"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR,
    )

    sk = create_skaffold_configuration(
        root_paths=root_paths, helm_values=values, output_path=out_folder
    )

    # Look in sk
    sk.get("build").get("artifacts")

    def get_buildargs(name) -> dict[str, str]:
        f = [e["docker"]["buildArgs"] for e in sk["build"]["artifacts"] if f"applications/{name}" in e["context"]]
        if len(f) > 0:
            return f[0]
        return {}

    samples_buildargs = get_buildargs("samples")
    assert samples_buildargs["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert samples_buildargs["NODE"] == "node:22-alpine"

    myapp_buildargs = get_buildargs("myapp")
    assert myapp_buildargs["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert myapp_buildargs["NODE"] == "node:22-alpine"
