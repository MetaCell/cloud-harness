import re
from keycloak import KeycloakError
from .keycloak import AuthClient
from cloudharness.applications import get_current_configuration
from cloudharness_model.models import ApplicationConfig
from cloudharness import log

from .user_attributes import UserNotFound, _filter_attrs, _construct_attribute_tree, _compute_attributes_from_tree, get_user_attributes
# quota tree node to hold the tree quota attributes


def get_group_quotas(group, application_config: ApplicationConfig):
    base_quotas = application_config.get("harness", {}).get("quotas", {})
    valid_keys_map = {key for key in base_quotas}
    return _compute_attributes_from_tree(_construct_attribute_tree([group], valid_keys_map))


def attribute_to_quota(attr_value: str):
    return float(re.sub("[^0-9.]", "", attr_value) if type(attr_value) is str else attr_value)


def get_user_quotas(application_config: ApplicationConfig = None, user_id: str = None) -> dict:
    """Get the user quota from Keycloak and application

    Args:
        application_config (ApplicationConfig): the application config to use for getting the quotas
        user_id (str): the Keycloak user id or username to get the quotas for

    Returns:
        dict: key/value pairs of the user quota

    Example:
        {'quota-ws-maxcpu': 1000, 'quota-ws-open': 10, 'quota-ws-max': 8}
    """
    if not application_config:
        application_config = get_current_configuration()
    base_quotas = application_config.get("harness", {}).get("quotas", {})

    valid_keys_map = {key for key in base_quotas}

    try:
        return get_user_attributes(user_id, valid_keys=valid_keys_map, default_attributes=base_quotas)

    except UserNotFound as e:
        log.warning("Quotas not available: error retrieving user: %s", user_id)
        return base_quotas
