import os
import jwt
import json
import requests
from flask import current_app, request
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakAuthenticationError
from cloudharness import log
from cloudharness.utils import env

try:
    from cloudharness.utils.config import CloudharnessConfig as conf, ALLVALUES_PATH
    from cloudharness.applications import get_configuration
    accounts_app = get_configuration('accounts')
    AUTH_REALM = conf.get_namespace()
    SERVER_URL = accounts_app.get_service_address() + '/auth/'
    if not os.environ.get('KUBERNETES_SERVICE_HOST', None):
        # running outside kubernetes
        SERVER_URL = accounts_app.get_public_address() + '/auth/'
    SERVER_URL = 'http://accounts.ifn.dev.metacell.us/auth/'
    USER = accounts_app.admin['user']
    PASSWD = accounts_app.admin['pass']
except:
    log.error("Error on cloudharness configuration. Check that the values file %s your deployment.",
              ALLVALUES_PATH, exc_info=True)


def with_refreshtoken(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except KeycloakAuthenticationError:
            self.refresh_token()
            return func(self, *args, **kwargs)
    return wrapper


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
    __public_key = None

    @staticmethod
    def _get_keycloak_user_id():
        bearer = request.headers.get('Authorization', None)
        current_app.logger.debug(f'Bearer: {bearer}')
        if not bearer or bearer == 'Bearer undefined':
            if current_app.config['ENV'] == 'development':
                # when development and not using KeyCloak (no current user),
                # get id from X-Current-User-Id header
                keycloak_user_id = request.headers.get(
                    "X-Current-User-Id", os.environ.get("CH_CURRENT_USER_ID", -1))
            else:
                keycloak_user_id = "-1"  # No authorization --> no user
        else:
            token = bearer.split(' ')[1]
            keycloak_user_id = AuthClient.decode_token(token)['sub']
        return keycloak_user_id

    def __init__(self):
        """
        Init the class and checks the connectivity to the KeyCloak server
        """
        # test if we can connect to the Keycloak server
        dummy_client = self.get_admin_client()
        self._current_user = None
        self._current_user_realm_roles = None
        self._current_user_client_roles = {}

    def get_admin_client(self):
        """
        Setup and return a keycloak admin client

        The client will connect to the Keycloak server with the default admin credentials
        and connects to the 'master' realm. The client uses the application realm for read/write
        to the Keycloak server

        :return: KeycloakAdmin
        """
        if not getattr(self, "_admin_client", None):
            self._admin_client = KeycloakAdmin(
                server_url=SERVER_URL,
                username=USER,
                password=PASSWD,
                realm_name=AUTH_REALM,
                user_realm_name='master',
                verify=True)
        return self._admin_client

    def refresh_token(self):
        try:
            self._admin_client.refresh_token()
        except Exception as e:
            # reset the internal admin client to create a new one
            self._admin_client = None
            self.get_admin_client()

    @classmethod
    def get_public_key(cls):
        if not cls.__public_key:
            AUTH_PUBLIC_KEY_URL = os.path.join(
                SERVER_URL, "realms", AUTH_REALM)

            KEY = json.loads(requests.get(AUTH_PUBLIC_KEY_URL,
                                          verify=False).text)['public_key']
            cls.__public_key = b"-----BEGIN PUBLIC KEY-----\n" + \
                str.encode(KEY) + b"\n-----END PUBLIC KEY-----"
        return cls.__public_key

    @classmethod
    def decode_token(cls, token):
        """
        Check and retrieve authentication information from custom bearer token.
        Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
        'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

        :param token Token provided by Authorization header
        :type token: str
        :return: Decoded token information or None if token is invalid
        :rtype: dict | None
        """

        decoded = jwt.decode(token, cls.get_public_key(),
                             algorithms='RS256', audience='account')
        return decoded

    @with_refreshtoken
    def get_client(self, client_name):
        """
        Return the KC client

        ClientRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_clientrepresentation

        :param client_name: Name of the client to retrieve
        :return: ClientRepresentation or False when not found
        """
        admin_client = self.get_admin_client()
        client_id = admin_client.get_client_id(client_name)
        client = admin_client.get_client(client_id)
        return client

    @with_refreshtoken
    def create_client(self,
                      client_name,
                      protocol="openid-connect",
                      enabled=True,
                      public=True,
                      standard_flow_enabled=True,
                      direct_access_grants_enable=True,
                      redirect_uris=["*"],
                      web_origins=["*", "+"]):
        """
        Creates a new KC client

        :param client_name: Name of the client
        :param protocol: defaults to openid-connect
        :param enabled: defaults to True
        :param public: defaults to True
        :param standard_flow_enabled: defaults to True
        :param direct_access_grants_enable: defaults to True
        :param redirect_uris: defaults to ["*"],
        :param web_origins: defaults to ["*","+"]
        :return: True on success or exception
        """
        admin_client = self.get_admin_client()
        x = admin_client.create_client({
            'id': client_name,
            'name': client_name,
            'protocol': protocol,
            'enabled': enabled,
            'publicClient': public,
            'standardFlowEnabled': standard_flow_enabled,
            'directAccessGrantsEnabled': direct_access_grants_enable,
            'redirectUris': redirect_uris,
            'webOrigins': web_origins
        })
        return True

    @with_refreshtoken
    def create_client_role(self, client_id, role):
        """
        Creates a new client role if not exists

        :param client_id: the id of the client under which the role will be created
        :param role: the name of the client role
        :return: True on success, False on error
        """
        admin_client = self.get_admin_client()
        admin_client.create_client_role(
            client_id,
            {
                'name': role,
                'clientRole': True
            }
        )
        return True

    @with_refreshtoken
    def get_group(self, group_id, with_members=False):
        """
        Return the group in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :param with_members: If set the members (users) of the group are added to the group. Defaults to False
        :return: GroupRepresentation + UserRepresentation
        """
        admin_client = self.get_admin_client()
        group = admin_client.get_group(group_id)
        if with_members:
            members = admin_client.get_group_members(group_id)
            for user in members:
                user.update(
                    {'userGroups': admin_client.get_user_groups(user['id'])})
                user.update(
                    {'realmRoles': admin_client.get_realm_roles_of_user(user['id'])})
            group.update({'members': members})
        return group

    @with_refreshtoken
    def get_groups(self, with_members=False):
        """
        Return a list of all groups in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :param with_members: If set the members (users) of the group(s) are added to the group. Defaults to False
        :return: List(GroupRepresentation)
        """
        admin_client = self.get_admin_client()
        groups = []
        for group in admin_client.get_groups():
            groups.append(self.get_group(group['id'], with_members))
        return groups

    @with_refreshtoken
    def get_users(self, query=None):
        """
        Return a list of all users in the application realm

        UserRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :param query: query filtering the users see https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_users_resource
        :return: List(UserRepresentation + GroupRepresentation)
        """
        admin_client = self.get_admin_client()
        users = []
        for user in admin_client.get_users(query=query):
            user.update(
                {'userGroups': admin_client.get_user_groups(user['id'])})
            user.update(
                {'realmRoles': admin_client.get_realm_roles_of_user(user['id'])})
            users.append(user)
        return users

    @with_refreshtoken
    def get_user(self, user_id):
        """
        Get the user including the user groups

        :param user_id: User id

        UserRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :return: UserRepresentation + GroupRepresentation
        """
        admin_client = self.get_admin_client()
        user = admin_client.get_user(user_id)
        user.update({'userGroups': admin_client.get_user_groups(user_id)})
        user.update(
            {'realmRoles': admin_client.get_realm_roles_of_user(user_id)})
        return user

    @with_refreshtoken
    def get_user_realm_roles(self, user_id):
        """
        Get the user including the user roles within the current realm

        :param user_id: User id

        RoleRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_rolerepresentation

        :return: (array RoleRepresentation)
        """
        admin_client = self.get_admin_client()
        return admin_client.get_realm_roles_of_user(user_id)

    def get_current_user(self):
        """
        Get the current user including the user groups

        UserRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_grouprepresentation

        :return: UserRepresentation + GroupRepresentation
        """
        if self._current_user:
            return self._current_user
        self._current_user = self.get_user(self._get_keycloak_user_id())
        return self._current_user

    def get_current_user_realm_roles(self):
        """
        Get the user including the user roles within the current realm

        :param user_id: User id

        RoleRepresentation
        https://www.keycloak.org/docs-api/8.0/rest-api/index.html#_rolerepresentation

        :return: (array RoleRepresentation)
        """
        if self._current_user_realm_roles:
            return self._current_user_realm_roles
        self._current_user_realm_roles = self.get_user_realm_roles(self._get_keycloak_user_id())
        return self._current_user_realm_roles

    @with_refreshtoken
    def get_user_client_roles(self, user_id, client_name):
        """
        Get the user including the user resource access

        :param user_id: User id
        :param client_name: Client name
        :return: (array RoleRepresentation)
        """
        admin_client = self.get_admin_client()
        client_id = admin_client.get_client_id(client_name)
        return admin_client.get_client_roles_of_user(user_id, client_id)

    def get_current_user_client_roles(self, client_name):
        """
        Get the user including the user resource access

        :param client_name: Client name
        :return: UserRepresentation + GroupRepresentation
        """
        if self._current_user_client_roles[client_name]:
            return self._current_user_client_roles[client_name]

        cur_user_id = self._get_keycloak_user_id()
        self._current_user_client_roles.update({client_name, self.get_user_client_roles(cur_user_id, client_name)})
        return self._current_user_client_roles[client_name]

    def user_has_client_role(self, user_id, client_name, role):
        """
        Tests if the user has the given role within the given client

        :param user_id: User id
        :param client_name: Name of the client
        :param role: Name of the role
        :return: (array RoleRepresentation)
        """
        roles = [user_client_role for user_client_role in self.get_user_client_roles(
            user_id, client_name) if user_client_role['name'] == role]
        return roles != []

    def user_has_realm_role(self, user_id, role):
        """
        Tests if the user has the given role within the current realm

        :param user_id: User id
        :param role: Name of the role
        :return: (array RoleRepresentation)
        """
        roles = [user_realm_role for user_realm_role in self.get_user_realm_roles(
            user_id) if user_realm_role['name'] == role]
        return roles != []

    def current_user_has_client_role(self, client_name, role):
        """
        Tests if the current user has the given role within the given client

        :param client_name: Name of the client
        :param role: Name of the role
        :return: (array RoleRepresentation)
        """
        return self.user_has_client_role(
            self._get_keycloak_user_id(),
            client_name,
            role)

    def current_user_has_realm_role(self, role):
        """
        Tests if the current user has the given role within the current realm

        :param role: Name of the role
        :return: (array RoleRepresentation)
        """
        return self.user_has_realm_role(
            self._get_keycloak_user_id(),
            role)

    @with_refreshtoken
    def get_client_role_members(self, client_name, role):
        """
        Get all users for the specified client and role

        :param client_name: Client name
        :param role: Role name
        :return: List(UserRepresentation)
        """
        admin_client = self.get_admin_client()
        client_id = admin_client.get_client_id(client_name)
        return admin_client.get_client_role_members(client_id, role)

    @with_refreshtoken
    def user_add_update_attribute(self, user_id, attribute_name, attribute_value):
        """
        Adds or when exists updates the attribute to/of the User with the attribute value

        param user_id: id of the user
        param attribute_name: name of the attribute to add/update
        param attribute_value: value of the attribute
        :return: boolean True on success
        """
        admin_client = self.get_admin_client()
        user = self.get_user(user_id)
        attributes = user.get('attributes', {})
        attributes[attribute_name] = attribute_value
        admin_client.update_user(
            user_id,
            {
                'attributes': attributes
            })
        return True

    @with_refreshtoken
    def user_delete_attribute(self, user_id, attribute_name):
        """
        Deletes the attribute to/of the User with the attribute value

        param user_id: id of the user
        param attribute_name: name of the attribute to delete
        :return: boolean True on success, False is attribute not in user attributes
        """
        admin_client = self.get_admin_client()
        user = self.get_user(user_id)
        attributes = user.get('attributes', None)
        if attributes and attribute_name in attributes:
            del attributes[attribute_name]
            admin_client.update_user(
                user_id,
                {
                    'attributes': attributes
                })
            return True
        return False
