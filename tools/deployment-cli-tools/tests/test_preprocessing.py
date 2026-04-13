import copy
import shutil
import os
import tempfile

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


def test_task_file_changes_trigger_different_tag():
    """Modifying a file under applications/*/tasks/*/* must produce a different
    hash-based tag for the corresponding task image."""

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT], output_path=OUT, include=['workflows'],
        domain="my.local", namespace='test', env='dev', local=False,
        tag=None, registry='reg',
    )

    # Pick a task image that lives under applications/workflows/tasks/
    task_key = 'workflows-notify-queue'
    assert task_key in values[KEY_TASK_IMAGES], (
        f"Expected '{task_key}' in task-images; got {list(values[KEY_TASK_IMAGES].keys())}"
    )

    # --- first run: compute tags on the original tree ---
    preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT], helm_values=values,
        merge_build_path=MERGE_BUILD_DIR,
    )
    values_before = copy.deepcopy(values)
    generate_hash_based_image_tags(
        root_paths=[CLOUDHARNESS_ROOT], helm_values=values_before,
        merge_build_path=MERGE_BUILD_DIR,
    )
    tag_before = values_before[KEY_TASK_IMAGES][task_key]

    # --- mutate a task file and recompute ---
    task_dir = os.path.join(
        CLOUDHARNESS_ROOT, 'applications', 'workflows', 'tasks', 'notify-queue',
    )
    tmp_file = os.path.join(task_dir, '_tag_test_tmp_file')
    try:
        with open(tmp_file, 'w') as f:
            f.write('trigger-tag-change')

        values_after = copy.deepcopy(values)
        generate_hash_based_image_tags(
            root_paths=[CLOUDHARNESS_ROOT], helm_values=values_after,
            merge_build_path=MERGE_BUILD_DIR,
        )
        tag_after = values_after[KEY_TASK_IMAGES][task_key]
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        if os.path.exists(MERGE_BUILD_DIR):
            shutil.rmtree(MERGE_BUILD_DIR)

    assert tag_before != tag_after, (
        f"Task image tag for '{task_key}' did not change after modifying task files. "
        f"Before: {tag_before}, After: {tag_after}"
    )
