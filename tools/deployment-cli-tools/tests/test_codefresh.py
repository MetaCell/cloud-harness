from ch_cli_tools.preprocessing import preprocess_build_overrides

from ch_cli_tools.helm import *
from ch_cli_tools.configurationgenerator import *
from ch_cli_tools.codefresh import *
from ch_cli_tools.secrets import is_cloudharness_managed, is_secret_config, secret_manager, secret_value

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = '/tmp/deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BUILD_MERGE_DIR = "./build/.overrides"

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
        assert "testprojectname/" in steps["cloudharness-base"]['image_name'], "cloudharness-base image should be overridden and take the main name"
        assert "cloudharness-base-debian" not in steps, "cloudharness-base image should not be included"
        assert "cloudharness-frontend-build" in steps, "cloudharness-frontend-build image should be included as dependency"
        assert "testprojectname/" in steps["cloudharness-frontend-build"]['image_name'], "cloudharness-frontend-build image is not overridden"

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
        assert step['dockerfile'].endswith('dev.Dockerfile'), f"myapp should use dev.Dockerfile but got {step['dockerfile']}"
        assert "testprojectname/" in step['image_name'], f"myapp image should have the project name coming from the chart in its path, is {step['image_name']}"
        for build_argument in step['build_arguments']:
            if build_argument.startswith("CLOUDHARNESS_FLASK="):
                assert "testprojectname" in build_argument, "Cloudharness flask image should have cloud-harness in its path"
                assert build_argument == "CLOUDHARNESS_FLASK=${{REGISTRY}}/testprojectname/cloudharness-flask:${{CLOUDHARNESS_FLASK_TAG}}", "Dependency is not properly set in the build arguments"

        assert os.path.samefile(step['working_directory'], os.path.join(
            RESOURCES, APPS_PATH, "myapp"))

        assert CD_UNIT_TEST_STEP in l1_steps, "Unit tests run step should be specified"
        assert CD_API_TEST_STEP in l1_steps, "Api steps are available in the dev env template"
        assert CD_E2E_TEST_STEP in l1_steps, "E2E steps are included in the dev env template"
        assert len(l1_steps[CD_UNIT_TEST_STEP]['steps']
                   ) == 2, "Two unit test steps are expected"
        assert 'myapp_ut' in l1_steps[CD_UNIT_TEST_STEP]['steps'], "Myapp test step is expected"
        tstep = l1_steps[CD_UNIT_TEST_STEP]['steps']['myapp_ut']
        assert tstep['image'] == r"${{REGISTRY}}/testprojectname/myapp:${{MYAPP_TAG}}", "The test image should be the one built for the current app"
        assert len(
            tstep['commands']) == 2, "Unit test commands are not properly loaded from the unit test configuration file"
        assert tstep['commands'][0] == "tox", "Unit test commands are not properly loaded from the unit test configuration file"
        assert len(l1_steps[CD_STEP_CLONE_DEPENDENCIES]['steps']) == 3, "3 clone steps should be included as we have 2 dependencies from myapp, plus cloudharness"

        publish_base_step = l1_steps[CD_STEP_PUBLISH]['steps']['publish_cloudharness-base']
        assert publish_base_step['when']['condition']['all']['skipPublish'] == "includes('${{CLOUDHARNESS_BASE_PUBLISH_SKIP}}', '{{CLOUDHARNESS_BASE_PUBLISH_SKIP}}') == true"
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
                assert "test-${{NAMESPACE_BASENAME}}" in cmd
                assert "-i samples" in cmd

    finally:
        shutil.rmtree(BUILD_MERGE_DIR)


def test_test_images_built_only_when_tests_exist_in_project_apps():
    """Test images are built iff the corresponding test type is enabled on at least one app.

    Positive case: app in RESOURCES (not CH) with e2e enabled → test-e2e must be built even
    though the test image lives in cloud-harness (root_paths[0]).

    Negative case: same app without e2e enabled → test-e2e must NOT be built.

    Regression: the test image search was done per root_path, so if the apps with tests are in
    root_path[1] (project) and the test images are in root_path[0] (cloud-harness), the images
    were never found because scale was empty when root_path[0] was scanned.
    """
    def _build_steps(e2e_enabled):
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
        root_paths = preprocess_build_overrides(
            root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
            helm_values=values,
            merge_build_path=BUILD_MERGE_DIR
        )
        build_included = [app['harness']['name']
                          for app in values['apps'].values() if 'harness' in app]
        values.apps["myapp"].harness.test.e2e.enabled = e2e_enabled
        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 envs=['dev', 'test'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)
        l1_steps = cf['steps']
        return {name: step for build_step in [STEP_0, STEP_1, STEP_2, STEP_3]
                if build_step in l1_steps
                for name, step in l1_steps[build_step]['steps'].items()}

    try:
        with_tests = _build_steps(e2e_enabled=True)
        assert "test-e2e" in with_tests, \
            "test-e2e image must be built when a project app has e2e tests, even if the image lives in cloud-harness"

        without_tests = _build_steps(e2e_enabled=False)
        assert "test-e2e" not in without_tests, \
            "test-e2e image must NOT be built when no app has e2e tests enabled"
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


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
        assert "APP_URL=https://www.${{DOMAIN}}" in test_step[
            'environment'], "APP_URL must be provided as environment variable"
        assert len(test_step['volumes']) == 1

        assert "test-api" in l1_steps[STEP_1]["steps"], "api tests image should be built"

        assert "test-api" in l1_steps[STEP_1]["steps"]["test-api"]["dockerfile"], "test-api image must be built from root context"
        api_steps = l1_steps['tests_api']['scale']
        test_step = api_steps["samples_api_test"]
        assert "APP_URL=https://www.${{DOMAIN}}/api" in test_step[
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

        all_build_steps = {k: v for k, v in l1_steps.items() if k.startswith(STEP_0[:-1])}
        built_images = {name for step in all_build_steps.values() for name in step.get("steps", {})}
        assert "test-e2e" not in built_images, "test-e2e image should not be built when no e2e tests are configured"
        assert "test-api" not in built_images, "test-api image should not be built when no api tests are configured"

    finally:
        shutil.rmtree(BUILD_MERGE_DIR)


def test_create_codefresh_configuration_app_without_base_build_dependency():
    """An app that has a Dockerfile but no build dependencies on task images must still
    be included in the build steps. Previously the apps directory was iterated only if
    task-images was non-empty, so apps with no base build dependency were silently skipped."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['accounts'],
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

        assert values.get('task-images') == {} or 'task-images' not in values, \
            "Precondition: accounts must not pull in any task images for this test to be meaningful"

        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)

        all_build_steps = {}
        for step_name in [STEP_0, STEP_1, STEP_2, STEP_3]:
            if step_name in cf['steps']:
                all_build_steps.update(cf['steps'][step_name].get('steps', {}))

        assert 'accounts' in all_build_steps, \
            f"accounts must be included in the build steps even when no base build dependency is specified. Got: {list(all_build_steps.keys())}"
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


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


def test_excluding_common_app_does_not_skip_common_images_dependencies():
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['myapp'],
        exclude=['common'],
        domain='my.local',
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )
    try:
        values[KEY_TASK_IMAGES]['my-common'] = 'reg/testprojectname/my-common:1'

        root_paths = preprocess_build_overrides(
            root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
            helm_values=values,
            merge_build_path=BUILD_MERGE_DIR
        )

        build_included = [app['harness']['name']
                          for app in values['apps'].values() if 'harness' in app]

        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 exclude=['common'],
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)

        all_build_steps = {
            step_name: step
            for build_step_name in [STEP_0, STEP_1, STEP_2, STEP_3]
            if build_step_name in cf['steps']
            for step_name, step in cf['steps'][build_step_name]['steps'].items()
        }

        assert 'my-common' in all_build_steps, \
            'Excluding app "common" must not skip the my-common image under infrastructure/common-images'
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_codefresh_db_connect_string_secret():
    """When an app has database.connect_string set to '', a custom_values entry must be added to the deployment step."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['myapp'],
        exclude=['events'],
        domain="my.local",
        namespace='test',
        env='connectstring',
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
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)
        custom_values = cf['steps']['deployment']['arguments']['custom_values']
        expected = "apps_myapp_harness_database_connect__string=\"${{MYAPP_DB_CONNECT_STRING}}\""
        assert expected in custom_values, \
            f"Expected custom_value entry for connect_string not found. Got: {custom_values}"
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_codefresh_secret_with_quotes():
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['myapp'],
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

        values.apps["myapp"].harness.secrets = {
            "settings_secret": "SECRET_KEY='replace-with-strong-shared-secret'"
        }

        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)

        custom_values = cf['steps']['deployment']['arguments']['custom_values']
        entry = next(
            value for value in custom_values
            if value.startswith("apps_myapp_harness_secrets_settings__secret=")
        )
        assert entry == 'apps_myapp_harness_secrets_settings__secret="${{SETTINGS__SECRET}}"'
        rendered = entry.replace(
            "${{SETTINGS__SECRET}}",
            values.apps["myapp"].harness.secrets["settings_secret"]
        )
        assert rendered == 'apps_myapp_harness_secrets_settings__secret="SECRET_KEY=\'replace-with-strong-shared-secret\'"'
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_sort_parallel_steps_alphabetically():
    """Sub-steps inside parallel steps must be sorted alphabetically by name."""
    steps = {
        'build_application_images_0': {
            'type': 'parallel',
            'stage': 'build',
            'steps': {
                'z-image': {'type': 'build'},
                'a-image': {'type': 'build'},
                'm-image': {'type': 'build'},
                'b-image': {'type': 'build'},
            }
        },
        'build_application_images_1': {
            'type': 'parallel',
            'stage': 'build',
            'steps': {
                'zz': {'type': 'build'},
                'aa': {'type': 'build'},
            }
        },
        'not_parallel': {
            'stage': 'prepare',
            'title': 'Not parallel',
        },
    }

    result = sort_parallel_steps(steps)

    # Parallel sub-steps are sorted alphabetically
    assert list(result['build_application_images_0']['steps'].keys()) == ['a-image', 'b-image', 'm-image', 'z-image']
    assert list(result['build_application_images_1']['steps'].keys()) == ['aa', 'zz']
    # Non-parallel steps are unaffected
    assert 'not_parallel' in result


def test_parallel_build_steps_sorted_alphabetically():
    """Sub-steps inside generated parallel build steps must be sorted alphabetically."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['samples', 'myapp', 'workflows'],
        exclude=['events'],
        domain='my.local',
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg',
    )
    try:
        root_paths = preprocess_build_overrides(
            root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
            helm_values=values,
            merge_build_path=BUILD_MERGE_DIR,
        )
        build_included = [app['harness']['name'] for app in values['apps'].values() if 'harness' in app]
        cf = create_codefresh_deployment_scripts(
            root_paths,
            include=build_included,
            envs=['dev'],
            base_image_name=values['name'],
            helm_values=values,
            save=False,
        )

        for step_name, step in cf['steps'].items():
            if step and isinstance(step, dict) and step.get('type') == 'parallel' and 'steps' in step:
                sub_step_names = list(step['steps'].keys())
                assert sub_step_names == sorted(sub_step_names), \
                    f"Sub-steps of '{step_name}' are not sorted alphabetically: {sub_step_names}"
    finally:
        import shutil
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_order_steps_by_stage():
    """Steps must be sorted according to the stages list; relative order within each stage is preserved."""
    stages = ['prepare', 'build', 'unittest', 'deploy', 'qa']

    steps = {
        'build_step_1': {'stage': 'build', 'title': 'Build 1'},
        'main_clone': {'stage': 'prepare', 'title': 'Clone'},
        'prepare_deployment': {'stage': 'prepare', 'title': 'Prepare'},
        'tests_unit': {'stage': 'unittest', 'title': 'Unit tests'},
        'build_step_2': {'stage': 'build', 'title': 'Build 2'},
        'deployment': {'stage': 'deploy', 'title': 'Deploy'},
        'tests_e2e': {'stage': 'qa', 'title': 'E2E tests'},
        'no_stage_step': {'title': 'No stage'},
    }

    result = order_steps_by_stage(steps, stages)
    step_names = list(result.keys())

    assert step_names.index('main_clone') < step_names.index('build_step_1'), "prepare must precede build"
    assert step_names.index('prepare_deployment') < step_names.index('build_step_1'), "prepare must precede build"
    assert step_names.index('build_step_1') < step_names.index('tests_unit'), "build must precede unittest"
    assert step_names.index('build_step_2') < step_names.index('tests_unit'), "build must precede unittest"
    assert step_names.index('tests_unit') < step_names.index('deployment'), "unittest must precede deploy"
    assert step_names.index('deployment') < step_names.index('tests_e2e'), "deploy must precede qa"

    # Relative order within each stage is preserved (stable sort)
    assert step_names.index('main_clone') < step_names.index('prepare_deployment'), "relative order within prepare preserved"
    assert step_names.index('build_step_1') < step_names.index('build_step_2'), "relative order within build preserved"

    # Steps without a stage come last
    assert step_names.index('no_stage_step') == len(step_names) - 1, "steps without a stage go to the end"


def test_steps_ordered_by_stage_in_generated_config():
    """The steps produced by create_codefresh_deployment_scripts must be ordered by stage."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['samples', 'myapp', 'workflows'],
        exclude=['events'],
        domain='my.local',
        namespace='test',
        env='dev',
        local=False,
        tag=1,
        registry='reg',
    )
    try:
        root_paths = preprocess_build_overrides(
            root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
            helm_values=values,
            merge_build_path=BUILD_MERGE_DIR,
        )
        build_included = [app['harness']['name'] for app in values['apps'].values() if 'harness' in app]
        cf = create_codefresh_deployment_scripts(
            root_paths,
            include=build_included,
            envs=['dev'],
            base_image_name=values['name'],
            helm_values=values,
            save=False,
        )

        stages = cf.get('stages', [])
        stage_order = {s: i for i, s in enumerate(stages)}
        steps = cf['steps']

        step_stage_indices = [
            stage_order.get(step.get('stage'), len(stages))
            for step in steps.values()
            if step and isinstance(step, dict)
        ]

        assert step_stage_indices == sorted(step_stage_indices), \
            "Steps are not ordered by stage. Got stages: " + str(
                [step.get('stage') for step in steps.values() if step and isinstance(step, dict)]
        )
    finally:
        import shutil
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_app_depends_on_app():

    root_paths = [CLOUDHARNESS_ROOT, RESOURCES]
    build_included = ['dependantapp']
    values = create_helm_chart(root_paths, output_path=OUT, domain="my.local",
                               env='', local=False, include=build_included, exclude=[])

    cf = create_codefresh_deployment_scripts([CLOUD_HARNESS_PATH, RESOURCES], include=build_included,
                                             envs=[],
                                             base_image_name=values['name'],
                                             helm_values=values, save=False)


def test_env_dockerfile_codefresh():
    """When a [env].Dockerfile exists it should be used in the codefresh build step."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['myapp'],
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
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)
        # myapp has dev.Dockerfile so it should be used
        myapp_step = cf['steps'][STEP_2]['steps']['myapp']
        assert myapp_step['dockerfile'].endswith('dev.Dockerfile'), \
            f"Expected dev.Dockerfile but got {myapp_step['dockerfile']}"
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_env_dockerfile_codefresh_fallback():
    """When no [env].Dockerfile exists the regular Dockerfile should be used."""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['samples'],
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

        # samples has no dev.Dockerfile, so it should fall back to Dockerfile
        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)
        all_build_steps = {
            step_name: step
            for build_step_name in [STEP_0, STEP_1, STEP_2, STEP_3]
            if build_step_name in cf['steps']
            for step_name, step in cf['steps'][build_step_name]['steps'].items()
        }
        assert 'samples' in all_build_steps, "samples should be in the build steps"
        samples_step = all_build_steps['samples']
        assert samples_step['dockerfile'] == 'Dockerfile', \
            f"Expected Dockerfile but got {samples_step['dockerfile']}"
        assert not samples_step['dockerfile'].endswith('dev.Dockerfile'), \
            "samples should not use dev.Dockerfile as it does not have one"
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_codefresh_paths_use_cloned_cloud_harness():
    """When cloud-harness root is outside the current directory (e.g. ../cloud-harness or
    an absolute path), paths in the generated codefresh YAML should use cloud-harness
    (the cloned location inside the pipeline working directory), not ../cloud-harness."""
    import tempfile

    for ch_root in [CLOUDHARNESS_ROOT, os.path.abspath(CLOUDHARNESS_ROOT)]:
        # Create a sibling directory to simulate running from a different project
        with tempfile.TemporaryDirectory(dir=os.path.dirname(CLOUDHARNESS_ROOT)) as tmp_project_dir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_project_dir)

                values = create_helm_chart(
                    [ch_root, RESOURCES],
                    output_path=OUT,
                    include=['samples'],
                    domain="my.local",
                    namespace='test',
                    env='dev',
                    local=False,
                    tag=1,
                    registry='reg'
                )

                root_paths = preprocess_build_overrides(
                    root_paths=[ch_root, RESOURCES],
                    helm_values=values,
                    merge_build_path=BUILD_MERGE_DIR
                )

                build_included = [app['harness']['name']
                                  for app in values['apps'].values() if 'harness' in app]

                cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                         envs=['dev'],
                                                         base_image_name=values['name'],
                                                         helm_values=values, save=False)

                # harness-deployment command must use cloud-harness, not the original path
                cmds = cf['steps']['prepare_deployment']['commands']
                harness_cmd = next(cmd for cmd in cmds if 'harness-deployment' in cmd)
                assert '../cloud-harness' not in harness_cmd, (
                    f"harness-deployment command should not reference ../cloud-harness "
                    f"(ch_root={ch_root!r}); got: {harness_cmd}"
                )
                assert os.path.abspath(ch_root) not in harness_cmd, (
                    f"harness-deployment command should not contain the absolute path "
                    f"(ch_root={ch_root!r}); got: {harness_cmd}"
                )
                assert 'cloud-harness' in harness_cmd, (
                    f"harness-deployment command should reference cloud-harness "
                    f"(ch_root={ch_root!r}); got: {harness_cmd}"
                )

                # working_directory in all build steps must not escape cwd or use absolute paths
                all_build_steps = {}
                for step_name in [STEP_0, STEP_1, STEP_2, STEP_3]:
                    if step_name in cf['steps']:
                        all_build_steps.update(cf['steps'][step_name]['steps'])

                for step_name, step in all_build_steps.items():
                    wd = step.get('working_directory', '')
                    assert not wd.startswith('../'), (
                        f"Build step '{step_name}' working_directory must not start with '../' "
                        f"(ch_root={ch_root!r}); got: {wd}"
                    )
                    assert not wd.startswith('./../'), (
                        f"Build step '{step_name}' working_directory must not start with './../' "
                        f"(ch_root={ch_root!r}); got: {wd}"
                    )
                    assert not os.path.isabs(wd), (
                        f"Build step '{step_name}' working_directory must not be absolute "
                        f"(ch_root={ch_root!r}); got: {wd}"
                    )
            finally:
                os.chdir(old_cwd)
                shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_codefresh_working_directory_uses_cloned_cloud_harness():
    """The working_directory for build steps that source images from cloud-harness must
    use ./cloud-harness/... for any form of input path (relative, absolute, with ..)."""
    import tempfile

    for ch_root in [CLOUDHARNESS_ROOT, os.path.abspath(CLOUDHARNESS_ROOT)]:
        with tempfile.TemporaryDirectory(dir=os.path.dirname(CLOUDHARNESS_ROOT)) as tmp_project_dir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_project_dir)

                values = create_helm_chart(
                    [ch_root, RESOURCES],
                    output_path=OUT,
                    include=['samples'],
                    domain="my.local",
                    namespace='test',
                    env='dev',
                    local=False,
                    tag=1,
                    registry='reg'
                )

                root_paths = preprocess_build_overrides(
                    root_paths=[ch_root, RESOURCES],
                    helm_values=values,
                    merge_build_path=BUILD_MERGE_DIR
                )

                build_included = [app['harness']['name']
                                  for app in values['apps'].values() if 'harness' in app]

                cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                         envs=['dev'],
                                                         base_image_name=values['name'],
                                                         helm_values=values, save=False)

                all_build_steps = {}
                for step_name in [STEP_0, STEP_1, STEP_2, STEP_3]:
                    if step_name in cf['steps']:
                        all_build_steps.update(cf['steps'][step_name]['steps'])

                ch_steps = {
                    name: step for name, step in all_build_steps.items()
                    if 'cloudharness' in name or name == 'samples'
                }
                assert ch_steps, "Expected at least one cloud-harness image build step"

                for step_name, step in ch_steps.items():
                    wd = step.get('working_directory', '')
                    assert not wd.startswith('../') and './../' not in wd, (
                        f"Cloud-harness build step '{step_name}' working_directory must not "
                        f"escape the current directory with '../' (ch_root={ch_root!r}); got: {wd}"
                    )
                    assert not os.path.isabs(wd), (
                        f"Cloud-harness build step '{step_name}' working_directory must not "
                        f"be absolute (ch_root={ch_root!r}); got: {wd}"
                    )
            finally:
                os.chdir(old_cwd)
                shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_codefresh_secret_managers():
    """Only the secrets handled by CloudHarness are exported as pipeline variables"""
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=OUT,
        include=['myapp'],
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

        values.apps["myapp"].harness.secrets = {
            "plain_secret": None,
            "static_random": "",
            "rich_secret": {"default": None},
            "rich_static_random": {"manager": "cloudharness", "default": ""},
            "op_secret": {"manager": "onepassword", "path": "vaults/v/items/i"},
            "unmanaged_secret": {"manager": None},
        }

        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 envs=['dev'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)

        custom_values = [value for value in cf['steps']['deployment']['arguments']['custom_values']
                         if value.startswith("apps_myapp_harness_secrets_")]
        assert custom_values == [
            'apps_myapp_harness_secrets_plain__secret="${{PLAIN__SECRET}}"',
            # the rich form nests the value under `default`
            'apps_myapp_harness_secrets_rich__secret_default="${{RICH__SECRET}}"',
        ]
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_wait_deployment_uses_the_workload_kind():
    """The wait step must roll out statefulset/<name> for apps rendered as StatefulSets and
    deployment/<name> for the others: `kubectl rollout status deployment/x` fails outright
    when x is a StatefulSet. Gatekeepers are always Deployments."""
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

        values.apps["samples"].harness.deployment.statefulset = True
        values.apps["accounts"].harness.deployment.statefulset = False
        values.apps["myapp"].harness.secured = True
        values.secured_gatekeepers = True

        cf = create_codefresh_deployment_scripts(root_paths, include=build_included,
                                                 envs=['dev', 'test'],
                                                 base_image_name=values['name'],
                                                 helm_values=values, save=False)

        commands = cf['steps'][CD_WAIT_STEP]['commands']

        samples = values.apps["samples"].harness.deployment.name
        accounts = values.apps["accounts"].harness.deployment.name
        assert f"kubectl rollout status statefulset/{samples}" in commands, \
            f"a statefulset app must be waited on as a statefulset. Got: {commands}"
        assert f"kubectl rollout status deployment/{samples}" not in commands, \
            f"a statefulset app must not be waited on as a deployment. Got: {commands}"
        assert f"kubectl rollout status deployment/{accounts}" in commands, \
            f"a non statefulset app must be waited on as a deployment. Got: {commands}"

        gk = f"{values.apps['myapp'].harness.subdomain}-gk"
        assert f"kubectl rollout status deployment/{gk}" in commands, \
            f"the gatekeeper is always a deployment. Got: {commands}"
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)


def test_codefresh_secret_managers_from_parsed_values():
    """Secrets read back from a parsed configuration are wrapped in the generated
    SecretDefinition union model: the helpers must see through it, or a manager delegated
    secret would be exported to the pipeline and overwritten by its value"""
    harness = ApplicationHarnessConfig.from_dict({
        'name': 'myapp',
        'secrets': {
            'plain_secret': None,
            'static_random': '',
            'rich_secret': {'default': None},
            'op_secret': {'manager': 'onepassword', 'path': 'vaults/v/items/i'},
            'unmanaged_secret': {'manager': None},
        },
    })

    definitions = harness.secrets
    assert type(definitions['op_secret']).__name__ == 'SecretDefinition', \
        "the test must exercise the wrapped form, not raw values"

    assert secret_manager(definitions['op_secret']) == 'onepassword'
    assert secret_manager(definitions['unmanaged_secret']) is None
    assert secret_manager(definitions['plain_secret']) == 'cloudharness'
    assert not is_cloudharness_managed(definitions['op_secret'])
    assert is_secret_config(definitions['rich_secret'])
    assert not is_secret_config(definitions['plain_secret'])
    assert secret_value(definitions['static_random']) == ''


def test_codefresh_source_images_build_args():
    """source_images entries (global base-image overrides) must be injected as build
    arguments for every build step, matching the behaviour of skaffold and Tilt."""
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

    source_images = values.get("source_images")
    assert source_images["KEYCLOAK"] == "myregistry.mykeycloak:99.9"
    assert source_images["NODE"] == "node:22-alpine"

    # CLOUDHARNESS_FLASK is also a build dependency of samples and myapp: a source_images
    # override for it must win over the dependency-derived build argument, not be shadowed by it.
    values["source_images"] = dict(source_images) | {"CLOUDHARNESS_FLASK": "myoverride/cloudharness-flask:9.9"}

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

        def get_build_step(name):
            for step_name, step in cf['steps'].items():
                if step_name.startswith(CD_BUILD_STEP_PARALLEL) and name in step.get('steps', {}):
                    return step['steps'][name]
            return None

        samples_build = get_build_step('samples')
        assert samples_build is not None, "samples build step not found"
        assert "KEYCLOAK=myregistry.mykeycloak:99.9" in samples_build['build_arguments']
        assert "NODE=node:22-alpine" in samples_build['build_arguments']
        assert "CLOUDHARNESS_FLASK=myoverride/cloudharness-flask:9.9" in samples_build['build_arguments']

        myapp_build = get_build_step('myapp')
        assert myapp_build is not None, "myapp build step not found"
        assert "KEYCLOAK=myregistry.mykeycloak:99.9" in myapp_build['build_arguments']
        assert "NODE=node:22-alpine" in myapp_build['build_arguments']
        assert "CLOUDHARNESS_FLASK=myoverride/cloudharness-flask:9.9" in myapp_build['build_arguments']
    finally:
        shutil.rmtree(BUILD_MERGE_DIR, ignore_errors=True)
