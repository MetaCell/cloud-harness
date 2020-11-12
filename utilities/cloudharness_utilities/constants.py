import os

NODE_BUILD_IMAGE = 'node:8.16.1-alpine'

HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')
ROOT = os.path.dirname(HERE)

HELM_PATH = "helm"
HELM_CHART_PATH = HELM_PATH

INFRASTRUCTURE_PATH = 'infrastructure'
STATIC_IMAGES_PATH = os.path.join(INFRASTRUCTURE_PATH, 'common-images')
BASE_IMAGES_PATH = os.path.join(INFRASTRUCTURE_PATH, 'base-images')
NEUTRAL_PATHS = ('src', 'tasks', 'server')
APPS_PATH = 'applications'
DEPLOYMENT_PATH = 'deployment'
CODEFRESH_PATH = 'codefresh/codefresh.yaml'

DEPLOYMENT_CONFIGURATION_PATH = 'deployment-configuration'

CODEFRESH_BUILD_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/codefresh-build-template.yaml'
CODEFRESH_TEMPLATE_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/codefresh-template.yaml'
CODEFRESH_REGISTRY = "r.cfcr.io/tarelli"

VALUES_MANUAL_PATH = 'values.yaml'
VALUE_TEMPLATE_PATH = f'{DEPLOYMENT_CONFIGURATION_PATH}/value-template.yaml'

CH_BASE_IMAGES = {'cloudharness-base': 'python:3.7-alpine', 'cloudharness-base-debian': 'python:3'}


BUILD_STEP_BASE = 'build_base_images'
BUILD_STEP_STATIC = 'build_static_images'
BUILD_STEP_PARALLEL = 'build_application_images'
BUILD_STEP_INSTALL = 'deployment'

