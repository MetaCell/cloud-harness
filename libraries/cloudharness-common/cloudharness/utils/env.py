import os

import yaml

from .. import log

from .config import conf

TEST = 'TEST'
PROD = 'PROD'

VARIABLE_IMAGE_REGISTRY = 'CH_IMAGE_REGISTRY'

SUFFIX_TAG = 'IMAGE_TAG'
SUFFIX_PORT = 'SERVICE_PORT'
SUFFIX_NAME = 'SERVICE_HOST'

DEFAULT_IMAGE_REGISTRY = ''

HERE = os.path.dirname(os.path.realpath(__file__))


def set_default_environment():
    values = conf.allvalues
    os.environ.update({v['name']: str(v["value"]) for v in values['env'] if v['name'] not in os.environ})


set_default_environment()

def get_namespace():
    try:
        namespace=conf.allvalues['namespace']
    except IndexError:
        namespace=''
    return namespace

namespace=get_namespace()

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
    tagged = f"{image_repository_name}:{get_image_tag(image_repository_name)}"
    registry = get_image_registry()
    if registry:
        return registry + '/' + tagged
    return tagged


def get_image_registry():
    try:
        return get_variable(VARIABLE_IMAGE_REGISTRY)
    except VariableNotFound as e:
        log.warning(f"Variable not found {VARIABLE_IMAGE_REGISTRY}. Using default: {DEFAULT_IMAGE_REGISTRY}")

        return DEFAULT_IMAGE_REGISTRY


def get_image_tag(application_name):
    try:

        return get_sub_variable(application_name, SUFFIX_TAG)
    except VariableNotFound as e:
        default_tag = get_variable('CH_IMAGE_TAG')
        log.warning(f"Image tag specification not found for {application_name}: variable not found {e.variable_name}. "
                    f"Using default: {default_tag}")

        return default_tag


def name_to_variable(application_name):
    return application_name.upper().replace('-', '_')


# CloudHarness Events
def get_cloudharness_events_client_id():
    accounts_app = conf.get_application_by_filter(name='accounts')
    return accounts_app.webclient.id


def get_cloudharness_events_service():
    return get_service_cluster_address('ARGO_GK')


def get_service_cluster_address(cloudharness_app_name):
    if use_public_services():
        return get_service_public_address(cloudharness_app_name)
    return get_sub_variable(cloudharness_app_name, SUFFIX_NAME) + ':' + get_sub_variable(cloudharness_app_name, SUFFIX_PORT)


def cluster_service_address(service_name):
    return  f'{service_name}.{namespace}.svc.cluster.local'


def use_public_services():
    try:
        return get_variable('CH_USE_PUBLIC').lower() == 'true'
    except VariableNotFound:
        return False

def get_sub_variable(*vars):
    return get_variable(name_to_variable('_'.join(vars)))


def get_service_public_address(app_name):
    return ".".join([get_sub_variable('CH', app_name, 'SUBDOMAIN'), get_public_domain()])


def get_public_domain():
    return get_variable('CH_DOMAIN')


def get_cloudharness_workflows_service_url():
    return get_service_public_address('WORKFLOWS')


def get_auth_service_cluster_address():
    return get_service_cluster_address('ACCOUNTS')


def get_auth_service_url():
    return get_service_public_address('ACCOUNTS')


def get_auth_realm():
    return get_variable('CH_ACCOUNTS_REALM')
