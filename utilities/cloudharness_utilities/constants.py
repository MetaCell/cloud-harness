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
NEUTRAL_PATHS = ('src', 'tasks', 'server')
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

CH_BASE_IMAGES = {'cloudharness-base': 'python:3.10-alpine', 'cloudharness-base-debian': 'python:3.10'}


CF_BUILD_STEP_BASE = 'build_base_images'
CF_BUILD_STEP_STATIC = 'build_static_images'
CF_BUILD_STEP_PARALLEL = 'build_application_images'
CF_STEP_INSTALL = 'deployment'
CF_STEP_PUBLISH = 'publish'
BUILD_FILENAMES = ('node_modules',)
