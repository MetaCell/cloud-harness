from ch_cli_tools.preprocessing import preprocess_build_overrides

from ch_cli_tools.helm import *
from ch_cli_tools.configurationgenerator import *
from ch_cli_tools.codefresh import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = '/tmp/deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BUILD_MERGE_DIR = "./build/test_deployment"

myapp_path = os.path.join(HERE, "resources/applications/myapp")
if not os.path.exists(os.path.join(myapp_path, "dependencies/a/.git")):
    os.makedirs(os.path.join(myapp_path, "dependencies/a/.git"))

STEP_0 = "build_application_images_0"
STEP_1 = "build_application_images_1"
STEP_2 = "build_application_images_2"
STEP_3 = "build_application_images_3"


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
    try:
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

        assert cf['steps']['main_clone']['title'] == 'Overridden', "Steps overriding is not working correctly"
        assert cf['steps']['main_clone']['type'] == 'git-clone', "Steps overriding missing values from the parent"

        l1_steps = cf['steps']

        step_build_base = l1_steps[STEP_0]
        assert step_build_base["type"] == "parallel"

        steps = l1_steps[STEP_0]["steps"]
        assert len(steps) == 7, "all images that do not depend on othe builds should be included in the first step"
        assert "cloudharness-base" in steps, "cloudharness-base image should be included as dependency"
        assert "cloudharness-base-debian" not in steps, "cloudharness-base image should not be included"
        assert "cloudharness-frontend-build" in steps, "cloudharness-frontend-build image should be included as dependency"

        step = steps["cloudharness-frontend-build"]
        assert os.path.samefile(step['working_directory'], CLOUDHARNESS_ROOT)
        assert os.path.samefile(os.path.join(step['working_directory'], step['dockerfile']),
                                os.path.join(CLOUDHARNESS_ROOT, BASE_IMAGES_PATH, "cloudharness-frontend-build", "Dockerfile"))

        step = steps["cloudharness-base"]
        assert step['working_directory'] == BUILD_MERGE_DIR, "Overridden base images should build inside the merge directory"
        assert os.path.samefile(
            os.path.join(step['working_directory'], step['dockerfile']),
            os.path.join(step['working_directory'],
                         BASE_IMAGES_PATH, "cloudharness-base", "Dockerfile")
        ), "Not overridden base images should be built from the base directory"

        assert "my-common" in steps, "my-common image should be included as dependency"

        step = steps["my-common"]
        assert step['dockerfile'] == "Dockerfile"
        assert os.path.samefile(step['working_directory'], os.path.join(
            RESOURCES, STATIC_IMAGES_PATH, "my-common"))

        step = steps["accounts"]
        assert step['dockerfile'] == "Dockerfile"
        assert os.path.samefile(step['working_directory'], os.path.join(
            BUILD_MERGE_DIR, APPS_PATH, "accounts"))

        steps = l1_steps[STEP_1]["steps"]
        assert "cloudharness-flask" in steps, "cloudharness-flask image should be included as dependency"
        assert "samples" not in steps, "samples depends on cloudharness-flask, so it should be included in the next step"

        step = steps["cloudharness-flask"]
        assert step['dockerfile'] == "Dockerfile"
        assert os.path.samefile(step['working_directory'], os.path.join(
            CLOUDHARNESS_ROOT, STATIC_IMAGES_PATH, "cloudharness-flask"))

        step = steps["workflows-notify-queue"]
        assert step['dockerfile'] == "Dockerfile"
        assert os.path.samefile(step['working_directory'], os.path.join(
            BUILD_MERGE_DIR, APPS_PATH, "workflows/tasks/notify-queue"))

        steps = l1_steps[STEP_2]["steps"]
        assert "myapp" in steps
        assert "samples" in steps
        assert "accounts" not in steps
        assert "workflows" in steps
        assert "events" not in steps

        step = steps["samples"]
        assert step['dockerfile'] == "Dockerfile"
        assert os.path.samefile(
            step['working_directory'], os.path.join(CLOUDHARNESS_ROOT, APPS_PATH, "samples"))

        step = steps["myapp"]
        assert step['dockerfile'] == "Dockerfile"
        for build_argument in step['build_arguments']:
            if build_argument.startswith("CLOUDHARNESS_FLASK="):
                assert "cloud-harness" in build_argument, "Cloudharness flask image should have cloud-harness in its path"
                assert build_argument == "CLOUDHARNESS_FLASK=${{REGISTRY}}/cloud-harness/cloudharness-flask:${{CLOUDHARNESS_FLASK_TAG}}", "Dependency is not properly set in the build arguments"

        assert os.path.samefile(step['working_directory'], os.path.join(
            RESOURCES, APPS_PATH, "myapp"))

        assert CD_UNIT_TEST_STEP in l1_steps, "Unit tests run step should be specified"
        assert CD_API_TEST_STEP in l1_steps, "Api steps are available in the dev env template"
        assert CD_E2E_TEST_STEP in l1_steps, "E2E steps are included in the dev env template"
        assert len(l1_steps[CD_UNIT_TEST_STEP]['steps']
                   ) == 2, "Two unit test steps are expected"
        assert 'myapp_ut' in l1_steps[CD_UNIT_TEST_STEP]['steps'], "Myapp test step is expected"
        tstep = l1_steps[CD_UNIT_TEST_STEP]['steps']['myapp_ut']
        assert tstep['image'] == r"${{REGISTRY}}/resources/myapp:${{MYAPP_TAG}}", "The test image should be the one built for the current app"
        assert len(
            tstep['commands']) == 2, "Unit test commands are not properly loaded from the unit test configuration file"
        assert tstep['commands'][0] == "tox", "Unit test commands are not properly loaded from the unit test configuration file"
        assert len(l1_steps[CD_STEP_CLONE_DEPENDENCIES]['steps']) == 3, "3 clone steps should be included as we have 2 dependencies from myapp, plus cloudharness"
    finally:
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
    try:
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
                assert "test_deployment" in cmd
                assert "-i samples" in cmd

    finally:
        shutil.rmtree(BUILD_MERGE_DIR)


def test_create_codefresh_configuration_tests():
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
    try:
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

        assert "test-e2e" in l1_steps[STEP_0]["steps"], "e2e tests image should be built"

        e2e_steps = l1_steps[CD_E2E_TEST_STEP]['scale']

        assert "samples_e2e_test" in e2e_steps, "samples e2e test step must be included"
        test_step = e2e_steps["samples_e2e_test"]
        assert "APP_URL=https://samples.${{DOMAIN}}" in test_step[
            'environment'], "APP_URL must be provided as environment variable"
        assert len(test_step['volumes']) == 1

        assert "test-api" in l1_steps[STEP_1]["steps"], "api tests image should be built"

        assert "test-api" in l1_steps[STEP_1]["steps"]["test-api"]["dockerfile"], "test-api image must be built from root context"
        api_steps = l1_steps['tests_api']['scale']
        test_step = api_steps["samples_api_test"]
        assert "APP_URL=https://samples.${{DOMAIN}}/api" in test_step[
            'environment'], "APP_URL must be provided as environment variable"
        assert len(test_step['volumes']) == 2

        assert any("allvalues.yaml" in v for v in test_step['volumes'])

        assert len(test_step["commands"]) == 2, "Both default and custom api tests should be run"

        st_cmd = test_step["commands"][0]
        assert "--pre-run cloudharness_test.apitest_init" in st_cmd, "Prerun hook must be specified in schemathesis command"
        assert "api/openapi.yaml" in st_cmd, "Openapi file must be passed to the schemathesis command"

        assert "-c all" in st_cmd, "Default check loaded is `all` on schemathesis command"
        assert "--hypothesis-deadline=" in st_cmd, "Custom parameters are loaded from values.yaml"

        test_step = api_steps["common_api_test"]
        for volume in test_step["volumes"]:
            assert "server" not in volume

        assert any("CLOUDHARNESS_BASE" in arg for arg in l1_steps[STEP_1]["steps"]["test-api"]
                   ["build_arguments"]), "Missing build dependency on api test image"

    finally:
        shutil.rmtree(BUILD_MERGE_DIR)

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env=['dev', 'test'],
        local=False,
        tag=1,
        registry='reg'
    )
    try:
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
        l1_steps = cf['steps']
        assert CD_API_TEST_STEP not in l1_steps, "Api steps are not included in any app"
        assert CD_E2E_TEST_STEP not in l1_steps, "E2E steps are not included in any app"

    finally:
        shutil.rmtree(BUILD_MERGE_DIR)


def test_create_codefresh_configuration_nobuild():
    values = create_helm_chart(
        [RESOURCES],
        output_path=OUT,
        include=['myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env=['dev', 'nobuild'],
        local=False,
        tag=1,
        registry='reg'
    )

    root_paths = preprocess_build_overrides(
        root_paths=[CLOUD_HARNESS_PATH, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_MERGE_DIR
    )

    build_included = [app['harness']['name']
                      for app in values['apps'].values() if 'harness' in app]

    cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                             envs=['dev', 'nobuild'],
                                             base_image_name=values['name'],
                                             helm_values=values, save=False)
    l1_steps = cf['steps']
    assert STEP_0 in l1_steps, "the task image should be included"
    assert len(l1_steps[STEP_0]["steps"]) == 1
    assert "myapp-mytask" in l1_steps[STEP_0]["steps"]
    assert STEP_1 not in l1_steps, "no image other than the task image should be included, because the included app  specifies a fixed image tag"

    assert "publish_myapp" not in l1_steps["publish"]["steps"]
    assert "publish_myapp-mytask" in l1_steps["publish"]["steps"]


def test_app_depends_on_app():

    root_paths = [CLOUDHARNESS_ROOT, RESOURCES]
    build_included = ['dependantapp']
    values = create_helm_chart(root_paths, output_path=OUT, domain="my.local",
                               env='', local=False, include=build_included, exclude=[])

    cf = create_codefresh_deployment_scripts([CLOUD_HARNESS_PATH, RESOURCES], include=build_included,
                                             envs=[],
                                             base_image_name=values['name'],
                                             helm_values=values, save=False)
