import os
import jwt
import sys
import json
import requests
from urllib.parse import urljoin
from typing import List
from flask import current_app, request
from keycloak import KeycloakAdmin

from typing import List
from urllib.parse import urljoin

from cloudharness.utils import env

try:
    from cloudharness.utils.config import CloudharnessConfig as conf
    accounts_app = conf.get_application_by_filter(name='accounts')[0]
    AUTH_REALM = env.get_auth_realm()
    SCHEMA = 'http'
    HOST = getattr(accounts_app,'subdomain')
    PORT = getattr(accounts_app,'port')
    USER = getattr(accounts_app.admin,'user')
    PASSWD = getattr(accounts_app.admin,'pass')
except:
    AUTH_REALM = 'mnp'
    SCHEMA = 'https'
    HOST = 'accounts.mnp.metacell.us'
    PORT = '443'
    USER = 'mnp'
    PASSWD = 'metacell'

SERVER_URL = f'{SCHEMA}://{HOST}:{PORT}/auth/'

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

    decoded = AuthClient.decode_token(token)
    valid = 'offline_access' in decoded['realm_access']['roles']
    current_app.logger.debug(valid)
    return {'uid': 'user_id'}


class AuthClient():

    @staticmethod
    def _get_keycloak_admin_client():
        """
        Setup and return a keycloak admin client
        
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

    @staticmethod
    def _get_keycloak_user_id():
        bearer = request.headers.get('Authorization', None)
        current_app.logger.debug(f'Bearer: {bearer}')
        if not bearer or bearer == 'Bearer undefined':
            decoded_token = None
            keycloak_user_id = -1  # No authorization --> no user
        else:
            token = bearer.split(' ')[1]
            decoded_token = AuthClient.decode_token(token)
            keycloak_user_id = decoded_token['sub']
        return keycloak_user_id

    @staticmethod
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
        AUTH_PUBLIC_KEY_URL = f'{SERVER_URL}/realms/{AUTH_REALM}'
        current_app.logger.debug(f'auth pub key url: {AUTH_PUBLIC_KEY_URL}')

        KEY = json.loads(requests.get(AUTH_PUBLIC_KEY_URL, verify=False).text)['public_key']
        KEY = b"-----BEGIN PUBLIC KEY-----\n" + str.encode(KEY) + b"\n-----END PUBLIC KEY-----"

        decoded = jwt.decode(token, KEY, algorithms='RS256', audience='account')
        return decoded

    def __init__(self):
        """
        Init the class and checks the connectivity to the KeyCloak server
        """
        # test if we can connect to the Keycloak server
        dummy_client = AuthClient._get_keycloak_admin_client()          

    @staticmethod
    def _get_group(admin_client, group_id, with_members=False):
        group = admin_client.get_group(group_id)
        if with_members:
            members = admin_client.get_group_members(group_id)
            group.update({'members': members})
        return group

    @staticmethod
    def get_groups(with_members=False):
        """
        Return a list of all groups in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :param with_members: If set the members (users) of the group(s) are added to the group. Defaults to False
        :return: List(GroupRepresentation)
        """
        admin_client = AuthClient._get_keycloak_admin_client()
        groups = []
        for group in admin_client.get_groups():
            groups.append(AuthClient._get_group(admin_client, group['id'], with_members))
        return groups

    @staticmethod
    def get_users():
        """
        Return a list of all users in the application realm

        UserRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :return: List(UserRepresentation + GroupRepresentation)
        """
        admin_client = AuthClient._get_keycloak_admin_client()
        users = []
        for user in admin_client.get_users():
            user.update({'userGroups': admin_client.get_user_groups(user['id'])})
            users.append(user)
        return users

    @staticmethod
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
        admin_client = AuthClient._get_keycloak_admin_client()
        user = admin_client.get_user(user_id)
        user.update({'userGroups': admin_client.get_user_groups(user_id)})
        return user

    @staticmethod
    def get_current_user():
        """
        Get the current user including the user groups

        UserRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :return: UserRepresentation + GroupRepresentation
        """
        return AuthClient.get_user(AuthClient._get_keycloak_user_id())
