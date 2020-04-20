import os
import jwt
import sys
import json
import requests
from urllib.parse import urljoin
from typing import List
from flask import current_app
from cloudharness.utils import env

def decode_token(token):
    """
    Check and retrieve authentication information from custom bearer token.
    Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
    'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

    :param token Token provided by Authorization header
    :type token: str
    :return: Decoded token information or None if token is invalid
    :rtype: dict | None
    """
    SCHEMA = 'https://'
    AUTH_DOMAIN = env.get_auth_service_cluster_address()
    AUTH_REALM = env.get_auth_realm()
    BASE_PATH = f"//{os.path.join(AUTH_DOMAIN, 'auth/realms', AUTH_REALM)}"
    AUTH_PUBLIC_KEY_URL = urljoin(SCHEMA, BASE_PATH)

    KEY = json.loads(requests.get(AUTH_PUBLIC_KEY_URL, verify=False).text)['public_key']

    KEY = f"-----BEGIN PUBLIC KEY-----\n{KEY}\n-----END PUBLIC KEY-----"

    try:
        decoded = jwt.decode(token, KEY, audience='accounts', algorithms='RS256')
    except:
        current_app.logger.debug(f"Error validating user: {sys.exc_info()}")
        return None

    valid = 'offline_access' in decoded['realm_access']['roles']
    current_app.logger.debug(valid)
    return {'uid': 'user_id'}