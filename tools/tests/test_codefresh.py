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
                                             envs=["dev"],
                                             base_image_name=values['name'],
                                             helm_values=values, save=False)

    assert "test_step" in cf

    l1_steps = cf['steps']
    step_build_base = l1_steps["build_base_images"]
    assert step_build_base["type"] == "parallel"

    steps = l1_steps["build_base_images"]["steps"]
    assert len(steps) == 2, "2 base images should be included as dependencies"
    assert "cloudharness-base" in steps, "cloudharness-base image should be included as dependency"
    assert "cloudharness-base-debian" not in steps, "cloudharness-base image should not be included"
    assert "cloudharness-frontend-build" in steps, "cloudharness-frontend-build image should be included as dependency"

    step = steps["cloudharness-frontend-build"]
    assert os.path.samefile(step['working_directory'], CLOUDHARNESS_ROOT)
    assert  os.path.samefile(os.path.join(step['working_directory'], step['dockerfile']), os.path.join(CLOUDHARNESS_ROOT,
        BASE_IMAGES_PATH, "cloudharness-frontend-build", "Dockerfile"))
    

    step = steps["cloudharness-base"]
    assert step['working_directory'] == BUILD_MERGE_DIR, "Overridden base images should build inside the merge directory"
    assert os.path.samefile(
        os.path.join(step['working_directory'], step['dockerfile']), 
        os.path.join(step['working_directory'], BASE_IMAGES_PATH, "cloudharness-base", "Dockerfile")
        ), "Not overridden base images should be built from the base directory"
    

    steps = l1_steps["build_static_images"]["steps"]
    assert len(steps) == 2, "2 static images should be included as dependencies"
    assert "cloudharness-flask" in steps, "cloudharness-flask image should be included as dependency"
    assert "my-common" in steps, "my-common image should be included as dependency"

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


    assert CD_UNIT_TEST_STEP in l1_steps, "Unit tests run step should be specified"
    assert len(l1_steps[CD_UNIT_TEST_STEP]['steps']) == 2, "Two unit test steps are expected"
    assert 'myapp_ut' in l1_steps[CD_UNIT_TEST_STEP]['steps'], "Myapp test step is expected"
    tstep = l1_steps[CD_UNIT_TEST_STEP]['steps']['myapp_ut']
    assert tstep['image'] == r"${{myapp}}", "The test image should be the one built for the current app"
    assert len(tstep['commands']) == 2, "Unit test commands are not properly loaded from the unit test configuration file"
    assert tstep['commands'][0] == "tox", "Unit test commands are not properly loaded from the unit test configuration file"

    shutil.rmtree(BUILD_MERGE_DIR)


def test_create_codefresh_configuration_multienv():
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['samples', 'myapp', "workflows"],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env=['dev', 'test'],
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
                                             envs=['dev', 'test'],
                                             base_image_name=values['name'],
                                             helm_values=values, save=False)

    assert cf['test_step'] == 'test'
    assert cf['test'] == True
    assert cf['dev'] == True
    for cmd in cf['steps']['prepare_deployment']['commands']:
        if 'harness-deployment' in cmd:
            assert '-e dev-test' in cmd
    

    shutil.rmtree(BUILD_MERGE_DIR)


def test_create_codefresh_configuration_e2etests():
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['samples', 'myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env=['dev', 'test'],
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
                                             envs=['dev', 'test'],
                                             base_image_name=values['name'],
                                             helm_values=values, save=False)

    # assert 'jest-puppeteer' in values['task-images']

    l1_steps = cf['steps']
    

    st_build_steps = l1_steps["build_static_images"]["steps"]

    assert "jest-puppeteer" in st_build_steps, "jest-puppeteer image should be built"

    e2e_steps = l1_steps['tests_e2e']['scale']

    assert "samples_e2e_test" in e2e_steps, "samples e2e test step must be included"
    test_step = e2e_steps["samples_e2e_test"]
    assert "APP_URL=https://samples.${{CF_SHORT_REVISION}}.${{DOMAIN}}" in test_step['environment'], "APP_URL must be provided as environment variable"
    assert len(test_step['volumes']) == 1


    assert "api-jest" in st_build_steps
    api_steps = l1_steps['tests_api']['scale']
    test_step = api_steps["samples_api_test"]
    assert "APP_URL=https://samples.${{CF_SHORT_REVISION}}.${{DOMAIN}}" in test_step['environment'], "APP_URL must be provided as environment variable"
    assert len(test_step['volumes']) == 1


    shutil.rmtree(BUILD_MERGE_DIR)