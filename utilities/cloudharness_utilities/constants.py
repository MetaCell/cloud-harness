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

CODEFRESH_PATH = 'codefresh/codefresh.yaml'

CODEFRESH_BUILD_PATH = 'deployment-templates/codefresh-build-template.yaml'
CODEFRESH_TEMPLATE_PATH = 'deployment-templates/codefresh-template.yaml'
CODEFRESH_REGISTRY = "r.cfcr.io/tarelli"

VALUES_MANUAL_PATH = 'values.yaml'
VALUE_TEMPLATE_PATH = 'deployment-templates/value-template.yaml'

CH_BASE_IMAGES = {'cloudharness-base': 'python:3.7-alpine', 'cloudharness-base-debian': 'python:3'}

K8S_IMAGE_EXCLUDE = ('accounts-keycloak-gatekeeper',)

BUILD_STEP_BASE = 'x1_build_base_image'
BUILD_STEP_STATIC = 'x2_static_build'
BUILD_STEP_PARALLEL = 'x3_parallel_build'
BUILD_STEP_INSTALL = 'x4_deployment'

DEPLOYMENT_CONFIGURATION_PATH = 'deployment-configuration'