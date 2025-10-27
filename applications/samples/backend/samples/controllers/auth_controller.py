import connexion
import six

from samples.models.valid import Valid  # noqa: E501
from samples import util


def valid_token():  # noqa: E501
    """Check if the token is valid. Get a token by logging into the dashboard

    Check if the token is valid  # noqa: E501


    :rtype: List[Valid]
    """
    from cloudharness.middleware import get_authentication_token
    token = get_authentication_token()
    if not token:
        return 'Unauthorized', 401
    return 'OK!'


def valid_cookie():  # noqa: E501
    """Check if the token is valid. Get a token by logging into the dashboard

    Check if the token is valid  # noqa: E501


    :rtype: List[Valid]
    """
    from cloudharness.middleware import get_authentication_token
    from cloudharness.auth import decode_token
    token = get_authentication_token()
    if not token:
        return 'Unauthorized', 401
    assert decode_token(token)
    return 'OK'
