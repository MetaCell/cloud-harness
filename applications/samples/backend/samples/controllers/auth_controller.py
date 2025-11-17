import connexion
import six

from samples import util


def valid_token():  # noqa: E501
    """Check if the token is valid. Get a token by logging into the dashboard

    Check if the token is valid  # noqa: E501


    :rtype: List[Valid]
    """
    from cloudharness.middleware import get_authentication_token
    token = get_authentication_token()
    return 'OK!'


def valid_cookie():  # noqa: E501
    """Check if the token is valid. Get a token by logging into the dashboard

    Check if the token is valid  # noqa: E501


    :rtype: List[Valid]
    """
    from cloudharness.middleware import get_authentication_token
    token = get_authentication_token()
    return 'OK'
