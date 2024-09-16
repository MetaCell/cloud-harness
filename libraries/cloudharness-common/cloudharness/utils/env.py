import os

import yaml

from .. import log

from .config import CloudharnessConfig as conf
from ..applications import get_configuration

TEST = 'TEST'
PROD = 'PROD'

VARIABLE_IMAGE_REGISTRY = 'CH_IMAGE_REGISTRY'

SUFFIX_TAG = 'IMAGE_TAG'
SUFFIX_PORT = 'SERVICE_PORT'
SUFFIX_NAME = 'SERVICE_HOST'

DEFAULT_IMAGE_REGISTRY = ''

HERE = os.path.dirname(os.path.realpath(__file__))


def set_default_environment():
    values = conf.get_configuration()

    if values and 'env' in values:
        os.environ.update({v['name']: str(v["value"]) for v in values['env'] if v['name'] not in os.environ})


set_default_environment()


def get_namespace():
    try:
        namespace = conf.get_configuration()['namespace']
    except:
        namespace = ''
    return namespace


namespace = get_namespace()


class VariableNotFound(Exception):
    def __init__(self, variable_name):
        self.variable_name = variable_name
        Exception.__init__(self, f'{variable_name} environment variable was not set.')


def get_cloudharness_variables():
    return {k: v for k, v in os.environ.items() if 'CH_' in k}


def get_variable(variable_name):
    variable_name = name_to_variable(variable_name)
    confstr = os.getenv(variable_name)
    if confstr is None:
        raise VariableNotFound(variable_name)
    return confstr


def get_image_full_tag(image_repository_name):
    return conf.get_image_tag(image_repository_name)


def get_image_registry():
    try:
        return get_variable(VARIABLE_IMAGE_REGISTRY)
    except VariableNotFound as e:
        log.warning(f"Variable not found {VARIABLE_IMAGE_REGISTRY}. Using default: {DEFAULT_IMAGE_REGISTRY}")

        return DEFAULT_IMAGE_REGISTRY


def name_to_variable(application_name):
    return application_name.upper().replace('-', '_')


# CloudHarness Events
def get_cloudharness_events_client_id():
    accounts_app = conf.get_application_by_filter(name='accounts')[0]
    return accounts_app.webclient.id


def get_cloudharness_events_service():
    return get_service_cluster_address('BOOTSTRAP')


def get_service_cluster_address(cloudharness_app_name):
    if use_public_services():
        return get_service_public_address(cloudharness_app_name)
    return cluster_service_address(cloudharness_app_name)


def cluster_service_address(service_name):
    return f'{service_name}.{namespace}.svc.cluster.local'


def use_public_services():
    try:
        return get_variable('CH_USE_PUBLIC').lower() == 'true'
    except VariableNotFound:
        return False


def get_sub_variable(*vars):
    return get_variable(name_to_variable('_'.join(vars)))


def get_service_public_address(app_name):
    return get_configuration(app_name).get_public_address()


def get_public_domain():
    return get_variable('CH_DOMAIN')


def get_cloudharness_workflows_service_url():
    return get_service_public_address('workflows')


def get_cloudharness_sentry_service_url():
    return get_configuration('sentry').get_public_address()


def get_sentry_service_cluster_address():
    return get_configuration('sentry').get_service_address()


def get_cloudharness_common_service_url():
    return get_configuration('common').get_public_address()


def get_common_service_cluster_address():
    common_app = get_configuration('common')
    return common_app.get_service_address()


def get_auth_service_cluster_address():
    return get_configuration('accounts').get_service_address()


def get_auth_service_url():
    return get_configuration('accounts').get_public_address()


def get_auth_realm():
    return get_variable('CH_ACCOUNTS_REALM')
