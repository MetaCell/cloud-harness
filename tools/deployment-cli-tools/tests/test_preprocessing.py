import shutil
import os

from ch_cli_tools.helm import *
from ch_cli_tools.preprocessing import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = '/tmp/deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
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

    assert not os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "accounts/deploy/values.yaml")), "deploy folder is in dockerignore, should not be copied"
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "workflows/tasks/new-task/Dockerfile"))
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "workflows/tasks/notify-queue/new-file"))
    assert os.path.exists(os.path.join(MERGE_BUILD_DIR, APPS_PATH, "workflows/tasks/notify-queue/Dockerfile"))

    # Assert that files from RESOURCES (last path) overwrite files from CLOUDHARNESS_ROOT
    merged_dockerfile = os.path.join(MERGE_BUILD_DIR, BASE_IMAGES_PATH, "cloudharness-base/Dockerfile")
    resources_dockerfile = os.path.join(RESOURCES, BASE_IMAGES_PATH, "cloudharness-base/Dockerfile")
    cloudharness_dockerfile = os.path.join(CLOUDHARNESS_ROOT, BASE_IMAGES_PATH, "cloudharness-base/Dockerfile")
    assert os.path.getsize(cloudharness_dockerfile) > 0, "CLOUDHARNESS_ROOT Dockerfile should have content"
    assert os.path.getsize(resources_dockerfile) == 0, "RESOURCES Dockerfile should be empty"
    assert os.path.getsize(merged_dockerfile) == 0, "Merged Dockerfile should match RESOURCES (last path wins)"

    shutil.rmtree(MERGE_BUILD_DIR)


def test_generate_hash_based_image_tags_uses_merged_content():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, include=['samples', 'myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False, tag=None, registry='reg')

    image_before = values[KEY_TASK_IMAGES]['cloudharness-base']
    assert image_before == 'reg/testprojectname/cloudharness-base'

    res = preprocess_build_overrides(root_paths=[CLOUDHARNESS_ROOT, RESOURCES], helm_values=values, merge_build_path=MERGE_BUILD_DIR)
    assert len(res) == 3

    generate_hash_based_image_tags(root_paths=[CLOUDHARNESS_ROOT, RESOURCES], helm_values=values, merge_build_path=MERGE_BUILD_DIR)

    image_after = values[KEY_TASK_IMAGES]['cloudharness-base']
    assert image_before != image_after

    shutil.rmtree(MERGE_BUILD_DIR)
