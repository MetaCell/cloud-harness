import shutil

from cloudharness_utilities.helm import *
from cloudharness_utilities.preprocessing import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = '/tmp/deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(HERE))
MERGE_BUILD_DIR = "/tmp/build"

def test_get_build_paths():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, include=['samples', 'myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, registry='reg')
    artifacts = get_build_paths(root_paths=[CLOUDHARNESS_ROOT, RESOURCES], helm_values=values, merge_build_path=MERGE_BUILD_DIR)
    assert 'cloudharness-base' in artifacts
    assert "events" not in artifacts
    assert "samples" in artifacts 

    assert artifacts['cloudharness-base'] == os.path.join(MERGE_BUILD_DIR, BASE_IMAGES_PATH, "cloudharness-base")
    assert artifacts['samples'] == os.path.join(CLOUDHARNESS_ROOT, APPS_PATH, "samples")

def test_preprocess_build_overrides():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, include=['samples', 'myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, registry='reg')


    res = preprocess_build_overrides(root_paths=[CLOUDHARNESS_ROOT, RESOURCES], helm_values=values, merge_build_path=MERGE_BUILD_DIR)
    assert len(res) == 3
    assert MERGE_BUILD_DIR in res[2]
    assert os.path.exists(MERGE_BUILD_DIR)

    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, BASE_IMAGES_PATH, "cloudharness-base/testfile")) 
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, BASE_IMAGES_PATH, "cloudharness-base/Dockerfile")) 
    assert not os.path.exists(os.path.join(MERGE_BUILD_DIR, BASE_IMAGES_PATH, "cloudharness-base-debian")) 
    assert not os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "events")) 

    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "accounts/deploy/values.yaml")) 
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "workflows/tasks/new-task/Dockerfile")) 
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "workflows/tasks/notify-queue/new-file")) 
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "workflows/tasks/notify-queue/Dockerfile")) 

    shutil.rmtree(MERGE_BUILD_DIR)
