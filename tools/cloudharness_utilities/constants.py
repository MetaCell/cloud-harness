import os

NODE_BUILD_IMAGE = 'node:8.16.1-alpine'

HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')
ROOT = os.path.dirname(HERE)

APPLICATION_TEMPLATE_PATH = 'application-templates'

HELM_PATH = "helm"
HELM_CHART_PATH = HELM_PATH

INFRASTRUCTURE_PATH = 'infrastructure'
STATIC_IMAGES_PATH = os.path.join(INFRASTRUCTURE_PATH, 'common-images')
BASE_IMAGES_PATH = os.path.join(INFRASTRUCTURE_PATH, 'base-images')
TEST_IMAGES_PATH = os.path.join(INFRASTRUCTURE_PATH, 'test-images')
NEUTRAL_PATHS = ('src', 'tasks', 'server', 'backend')
APPS_PATH = 'applications'
DEPLOYMENT_PATH = 'deployment'
CODEFRESH_PATH = 'codefresh/codefresh.yaml'
EXCLUDE_PATHS = ['node_modules', '.git', '.tox']

DEPLOYMENT_CONFIGURATION_PATH = 'deployment-configuration'

CF_BUILD_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/codefresh-build-template.yaml'
CF_TEMPLATE_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/codefresh-template.yaml'
CF_TEMPLATE_PUBLISH_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/codefresh-publish-template.yaml'

VALUES_MANUAL_PATH = 'values.yaml'
VALUE_TEMPLATE_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/value-template.yaml'

CH_BASE_IMAGES = {'cloudharness-base': 'python:3.9.10-alpine', 'cloudharness-base-debian': 'python:3.9.10'}


CD_BUILD_STEP_BASE = 'build_base_images'
CD_BUILD_STEP_STATIC = 'build_static_images'
CD_BUILD_STEP_PARALLEL = 'build_application_images'
CD_UNIT_TEST_STEP = 'tests_unit'
CD_STEP_INSTALL = 'deployment'
CD_WAIT_STEP = "wait_deployment"
CD_API_TEST_STEP = 'tests_api'
CD_E2E_TEST_STEP = 'tests_e2e'
CD_STEP_PUBLISH = 'publish'
BUILD_FILENAMES = ('node_modules',)

UNITTEST_FNAME = 'unit.yaml'
E2E_TESTS_DIRNAME = 'e2e'
API_TESTS_DIRNAME = 'api'
