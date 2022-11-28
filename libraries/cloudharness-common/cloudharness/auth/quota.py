from .keycloak import AuthClient
from cloudharness.applications import get_current_configuration
from cloudharness_model.models import ApplicationConfig


# quota tree node to hold the tree quota attributes
class QuotaNode:
    def __init__(self, name, attrs):
        self.attrs = attrs
        self.name = name
        self.children = []

    def addChild(self, child):
        self.children.append(child)


def _filter_quota_attrs(attrs, valid_keys_map):
    # only use the attributes defined by the valid keys map
    valid_attrs = {}
    if attrs is None:
        return valid_attrs
    for key in attrs:
        if key in valid_keys_map:
            # map to value
            valid_attrs.update({key: attrs[key][0]})
    return valid_attrs


def _construct_quota_tree(groups, valid_keys_map) -> QuotaNode:
    root = QuotaNode("root", {})
    for group in groups:
        r = root
        paths = group["path"].split("/")[1:]
        # loop through all segements except the last segment
        # the last segment is the one we want to add the attributes to
        for segment in paths[0 : len(paths) - 1]:
            for child in r.children:
                if child.name == segment:
                    r = child
                    break
            else:
                # no child found, add it with the segment name of the path
                n = QuotaNode(segment, {})
                r.addChild(n)
                r = n
        # add the child with it's attributes and last segment name
        n = QuotaNode(
            paths[len(paths) - 1],
            _filter_quota_attrs(group["attributes"], valid_keys_map)
        )
        r.addChild(n)
    return root


def _compute_quotas_from_tree(node: QuotaNode):
    """Recursively traverse the tree and find the quota per level
    the lower leafs overrule parent leafs values
    
    Args:
        node (QuotaNode): the quota tree of QuotaNodes of the user for the given application
        
    Returns:
        dict: key/value pairs of the quotas
        
    Example:
        {'quota-ws-maxcpu': 1000, 'quota-ws-open': 10, 'quota-ws-max': 8}

    Algorithm explanation:
      /Base {'quota-ws-max': 12345, 'quota-ws-maxcpu': 50, 'quota-ws-open': 1}\n
      /Base/Base 1/Base 1 1 {'quota-ws-maxcpu': 2, 'quota-ws-open': 10}\n
      /Base/Base 2 {'quota-ws-max': 8, 'quota-ws-maxcpu': 250}\n
      /Low CPU {'quota-ws-max': 3, 'quota-ws-maxcpu': 1000, 'quota-ws-open': 1}\n

      result: {'quota-ws-maxcpu': 1000, 'quota-ws-open': 10, 'quota-ws-max': 8}\n
      quota-ws-maxcpu from path "/Low CPU"\n
        --> overrules paths "/Base/Base 1/Base 1 1" and "/Base/Base 2" (higher value)\n
        --> /Base quota-ws-max is not used because this one is not the lowest
            leaf with this attribute (Base 1 1 and Base 2 are "lower")\n
      quota-ws-open from path "/Base/Base 1/Base 1 1"\n
      quota-ws-max from path "/Base/Base 2"\n
    """
    new_attrs = {}
    for child in node.children:
        child_attrs = _compute_quotas_from_tree(child)
        for key in child_attrs:
            try:
                child_val = float(child_attrs[key])
            except:
                # value not a float, skip (use 0)
                child_val = 0
            if not key in new_attrs or new_attrs[key] < child_val:
                new_attrs.update({key: child_val})
    for key in new_attrs:
        node.attrs.update({key: new_attrs[key]})
    return node.attrs


def get_user_quotas(application_config: ApplicationConfig =None, user_id: str=None) -> dict:
    """Get the user quota from Keycloak and application
    
    Args:
        application_config (ApplicationConfig): the application config to use for getting the quotas
        user_id (str): the Keycloak user id
    
    Returns:
        dict: key/value pairs of the user quota
        
    Example:
        {'quota-ws-maxcpu': 1000, 'quota-ws-open': 10, 'quota-ws-max': 8}
    """
    if not application_config:
        application_config = get_current_configuration()

    auth_client = AuthClient()
    if not user_id:
        user_id = auth_client.get_current_user()["id"]
    user = auth_client.get_user(user_id, with_details=True)

    valid_keys_map = []
    base_quotas = application_config.get("harness",{}).get("quotas", {})
    for key in base_quotas:
        valid_keys_map.append(key)
    
    group_quotas = _compute_quotas_from_tree(
        _construct_quota_tree(
            user["userGroups"],
            valid_keys_map))
    user_quotas = _filter_quota_attrs(user["attributes"], valid_keys_map)
    for key in group_quotas:
        if key not in user_quotas:
            user_quotas.update({key: group_quotas[key]})
    return user_quotas
