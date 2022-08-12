import shutil

from cloudharness_utilities.preprocessing import preprocess_build_overrides
from cloudharness_utilities.helm import *
from cloudharness_utilities.skaffold import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = '/tmp/deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(HERE))


def test_create_skaffold_configuration():
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
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
        output_path=OUT
    )
    assert os.path.exists(os.path.join(OUT, 'skaffold.yaml'))
    exp_apps = ('accounts', 'samples', 'workflows', 'myapp')
    assert len(sk['build']['artifacts']) == len(
        exp_apps) + len(values[KEY_TASK_IMAGES])
    assert 'reg' in sk['build']['artifacts'][0]['image']
    assert 'cloudharness' in sk['build']['artifacts'][0]['image']
    artifact_overrides = sk['deploy']['helm']['releases'][0]['artifactOverrides']
    for app in exp_apps:
        assert app in artifact_overrides[KEY_APPS]
    for img in values[KEY_TASK_IMAGES]:
        assert img in artifact_overrides[KEY_TASK_IMAGES]

    assert 'reg/cloudharness/cloudharness-base' in (
        a['image'] for a in sk['build']['artifacts'])
    assert 'reg/cloudharness/cloudharness-base-debian' not in (
        a['image'] for a in sk['build']['artifacts'])

    overrides = sk['deploy']['helm']['releases'][0]['overrides']
    assert overrides[KEY_APPS]['samples'][KEY_HARNESS][KEY_DEPLOYMENT]['command'] == [
        'python']
    assert overrides[KEY_APPS]['samples'][KEY_HARNESS][KEY_DEPLOYMENT]['args']

    assert 'reg' == artifact_overrides[KEY_APPS]['accounts'][KEY_HARNESS][KEY_DEPLOYMENT]['image'][0:3]
    assert 'harness' in artifact_overrides[KEY_APPS]['accounts'][KEY_HARNESS][KEY_DEPLOYMENT]['image']

    cloudharness_base_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == 'reg/cloudharness/cloudharness-base')
    assert cloudharness_base_artifact['context'] == BUILD_DIR
    assert 'requires' not in cloudharness_base_artifact

    cloudharness_flask_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == 'reg/cloudharness/cloudharness-flask')


    assert os.path.samefile(cloudharness_flask_artifact['context'], 
       join(CLOUDHARNESS_ROOT, 'infrastructure/common-images/cloudharness-flask')
    )

    assert len(cloudharness_flask_artifact['requires']) == 1

    samples_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == 'reg/cloudharness/samples'
    )
    assert os.path.samefile(samples_artifact['context'], join(CLOUDHARNESS_ROOT, 'applications/samples'))

    myapp_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == 'reg/cloudharness/myapp')
    assert os.path.samefile(myapp_artifact['context'], join(
        RESOURCES, 'applications/myapp'))

    accounts_artifact = next(
        a for a in sk['build']['artifacts'] if a['image'] == 'reg/cloudharness/accounts')
    assert os.path.samefile(accounts_artifact['context'], '/tmp/build/applications/accounts')


    # Custom unit tests
    assert len(sk['test']) == 2, 'Unit tests should be included'

    samples_test = sk['test'][0]
    assert samples_test['image'] == 'reg/cloudharness/samples', 'Unit tests for samples should be included'
    assert "samples/test" in samples_test['custom'][0]['command'], "The test command must come from values.yaml test/unit/commands"

    assert len(sk['test'][1]['custom']) == 2

    shutil.rmtree(OUT)
    shutil.rmtree(BUILD_DIR)
