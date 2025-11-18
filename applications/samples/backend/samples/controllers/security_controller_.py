from typing import List
from cloudharness.auth import decode_token
from cloudharness.middleware import set_authentication_token


def info_from_bearerAuth(token):
    """
    Check and retrieve authentication information from custom bearer token.
    Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
    'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

    :param token Token provided by Authorization header
    :type token: str
    :return: Decoded token information or None if token is invalid
    :rtype: dict | None
    """
    return {'uid': 'user_id'}


def info_from_cookieAuth(api_key):
    """
    Check and retrieve authentication information from cookie-based API key.
    This function is called by Connexion when cookieAuth security is used.

    :param api_key Token provided by the kc-access cookie
    :type api_key: str
    :return: Decoded token information or None if token is invalid
    :rtype: dict | None
    """
    if not api_key:
        return None

    # Set the authentication token in the middleware context
    # so that get_authentication_token() can access it
    set_authentication_token(api_key)

    # Decode and validate the token
    try:
        decoded = decode_token(api_key)
        if decoded:
            return decoded
    except Exception:
        pass

    return None
