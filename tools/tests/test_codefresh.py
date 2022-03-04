from cloudharness_utilities.preprocessing import preprocess_build_overrides

from cloudharness_utilities.helm import *
from cloudharness_utilities.codefresh import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = './deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD_MERGE_DIR = "./build/test_deployment"


def test_create_codefresh_configuration():
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['samples', 'myapp', "workflows"],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )

    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_MERGE_DIR
    )

    build_included = [app['harness']['name']
                      for app in values['apps'].values() if 'harness' in app]

    cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                             env="dev",
                                             base_image_name=values['name'],
                                             values_manual_deploy=values, save=False)

    assert "test_step" in cf

    l1_steps = cf['steps']
    step_build_base = l1_steps["build_base_images"]
    assert step_build_base["type"] == "parallel"

    steps = l1_steps["build_base_images"]["steps"]
    assert len(steps) == 2
    assert "cloudharness-base" in steps
    assert "cloudharness-base-debian" not in steps
    assert "cloudharness-frontend-build" in steps

    step = steps["cloudharness-frontend-build"]
    assert  os.path.samefile(step['dockerfile'], os.path.join(CLOUDHARNESS_ROOT,
        BASE_IMAGES_PATH, "cloudharness-frontend-build", "Dockerfile"))
    assert os.path.samefile(step['working_directory'], CLOUDHARNESS_ROOT)

    step = steps["cloudharness-base"]
    assert os.path.samefile(step['dockerfile'], os.path.join(BASE_IMAGES_PATH, "cloudharness-base", "Dockerfile"))
    assert step['working_directory'] == BUILD_MERGE_DIR

    steps = l1_steps["build_static_images"]["steps"]
    assert len(steps) == 2
    assert "cloudharness-flask" in steps
    assert "my-common" in steps

    step = steps["cloudharness-flask"]
    assert step['dockerfile'] == "Dockerfile"
    assert os.path.samefile(step['working_directory'], os.path.join(
        CLOUDHARNESS_ROOT, STATIC_IMAGES_PATH, "cloudharness-flask"))

    step = steps["my-common"]
    assert step['dockerfile'] == "Dockerfile"
    assert os.path.samefile(step['working_directory'], os.path.join(
        RESOURCES, STATIC_IMAGES_PATH, "my-common"))

    steps = l1_steps["build_application_images"]["steps"]
    assert len(steps) == 11
    assert "myapp" in steps
    assert "samples" in steps
    assert "accounts" in steps
    assert "workflows" in steps
    assert "workflows-notify-queue" in steps
    assert "workflows-new-task" in steps
    assert "events" not in steps

    step = steps["samples"]
    assert step['dockerfile'] == "Dockerfile"
    assert os.path.samefile(
        step['working_directory'], os.path.join(CLOUDHARNESS_ROOT, APPS_PATH, "samples"))

    step = steps["myapp"]
    assert step['dockerfile'] == "Dockerfile"
    assert os.path.samefile(step['working_directory'], os.path.join(
        RESOURCES, APPS_PATH, "myapp"))

    step = steps["accounts"]
    assert step['dockerfile'] == "Dockerfile"
    assert os.path.samefile(step['working_directory'], os.path.join(
        BUILD_MERGE_DIR, APPS_PATH, "accounts"))

    step = steps["workflows-notify-queue"]
    assert step['dockerfile'] == "Dockerfile"
    assert os.path.samefile(step['working_directory'], os.path.join(
        BUILD_MERGE_DIR, APPS_PATH, "workflows/tasks/notify-queue"))

    shutil.rmtree(BUILD_MERGE_DIR)