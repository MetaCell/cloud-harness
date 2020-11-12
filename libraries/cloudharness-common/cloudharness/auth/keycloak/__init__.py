import os
import jwt
import sys
import json
import requests
from urllib.parse import urljoin
from typing import List
from flask import current_app

from cloudharness.utils import env

from keycloak import KeycloakAdmin

try:
    from cloudharness.utils.config import CloudharnessConfig as conf
    accounts_app = conf.get_application_by_filter(name='accounts')[0]
    AUTH_REALM = env.get_auth_realm()
    AUTH_DOMAIN = env.get_auth_service_cluster_address()
    HOST = getattr(accounts_app,'subdomain')
    PORT = getattr(accounts_app,'port')
    USER = getattr(accounts_app.admin,'user')
    PASSWD = getattr(accounts_app.admin,'pass')
except:
    AUTH_REALM = 'mnp'
    AUTH_DOMAIN = 'localhost'
    HOST = 'localhost'
    PORT = '8080'
    USER = 'mnp'
    PASSWD = 'metacell'

SERVER_URL = f'http://{HOST}:{PORT}/auth/'

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

def _get_keycloak_admin_client():
    """ Setup and return a keycloak admin client
    
    The client will connect to the Keycloak server with the default admin credentials
    and connects to the 'master' realm. The client uses the application realm for read/write
    to the Keycloak server

    :return: KeycloakAdmin
    """
    # TODO: create an second admin user for API access (only)
    return KeycloakAdmin(server_url=SERVER_URL,
                         username=USER,
                         password=PASSWD,
                         realm_name=AUTH_REALM,
                         user_realm_name='master',
                         verify=True)

def get_groups():
    """
    Return a list of all groups in the application realm

    GroupRepresentation
    https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

    :return: List(GroupRepresentation)
    """
    keycloak_admin = _get_keycloak_admin_client()
    groups = []
    for group in keycloak_admin.get_groups():
        groups.append(keycloak_admin.get_group(group['id']))
    return groups

def get_users():
    """
    Return a list of all users in the application realm

    UserRepresentation
    https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

    GroupRepresentation
    https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

    :return: List(UserRepresentation + GroupRepresentation)
    """
    keycloak_admin = _get_keycloak_admin_client()
    users = []
    for user in keycloak_admin.get_users():
        user.update({'userGroups': keycloak_admin.get_user_groups(user['id'])})
        users.append(user)
    return users

def get_user(user_id):
    """
    Get the user including the user groups

    :param user_id: User id

    UserRepresentation
    https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

    GroupRepresentation
    https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

    :return: UserRepresentation + GroupRepresentation
    """
    keycloak_admin = _get_keycloak_admin_client()
    user = keycloak_admin.get_user(user_id)
    user.update({'userGroups': keycloak_admin.get_user_groups(user_id)})
    return user
