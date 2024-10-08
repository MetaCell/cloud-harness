import os
from typing import List
import jwt
import json
import requests

from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError

from cloudharness import log
from cloudharness.middleware import get_authentication_token
from cloudharness.models import UserGroup, User

from .exceptions import UserNotFound, InvalidToken, AuthSecretNotFound

try:
    from cloudharness.utils.config import CloudharnessConfig as conf, ALLVALUES_PATH
    from cloudharness.applications import get_configuration
except:
    log.error("Error on cloudharness configuration. Check that the values file %s your deployment.",
              ALLVALUES_PATH, exc_info=True)


def get_api_password() -> str:
    name = "api_user_password"
    AUTH_SECRET_PATH = os.environ.get(
        "AUTH_SECRET_PATH", "/opt/cloudharness/resources/auth")
    try:
        with open(os.path.join(AUTH_SECRET_PATH, name)) as fh:
            return fh.read()
    except:
        # if no secrets folder or file exists
        raise AuthSecretNotFound(name)


def with_refreshtoken(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except KeycloakAuthenticationError:
            self.refresh_token()
            return func(self, *args, **kwargs)
    return wrapper


def decode_token(token, **kwargs):
    """
    Check and retrieve authentication information from custom bearer token.
    Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
    'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

    :param token Token provided by Authorization header
    :type token: str
    :return: Decoded token information or None if token is invalid
    :rtype: dict | None
    """
    try:
        decoded = AuthClient.decode_token(token)
    except InvalidToken:
        return None
    return decoded


def get_server_url():
    accounts_app = get_configuration('accounts')

    if not os.environ.get('KUBERNETES_SERVICE_HOST', None):
        # running outside kubernetes
        return accounts_app.get_public_address() + '/auth/'
    return accounts_app.get_service_address() + '/auth/'


def get_auth_realm():
    return conf.get_namespace()


def get_token(username, password):
    conf = get_configuration("accounts")

    keycloak_openid = KeycloakOpenID(
        server_url=get_server_url(),
        realm_name=get_auth_realm(),
        client_id=conf["webclient"]["id"],
        client_secret_key=conf["webclient"]["secret"])
    return keycloak_openid.token(username, password)['access_token']


def is_uuid(s):
    import uuid
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


class AuthClient():
    __public_key = None

    @staticmethod
    def _get_keycloak_user_id():
        try:
            authentication_token = get_authentication_token()
        except LookupError:
            # this needs to be removed in future, for now we leave it for apps not using flask_init
            # in that case the contextvars aren't set by the Cloudharness Flask middleware
            log.warning(
                "Call to deprecated function, please use cloudharness.utils.server.flask_init to "
                "initialize your application."
            )
            from flask import request
            authentication_token = request.headers.get('Authorization', None)

        if not authentication_token or authentication_token == 'Bearer undefined':
            keycloak_user_id = "-1"  # No authorization --> no user
        else:
            token = authentication_token.split(' ')[-1]

            keycloak_user_id = AuthClient.decode_token(token)['sub']

        return keycloak_user_id

    def __init__(self, username=None, password=None):
        """
        Init the class and checks the connectivity to the KeyCloak server
        """

        self.user = username or os.getenv('ACCOUNTS_ADMIN_USERNAME', None) or "admin_api"
        self.passwd = password or os.getenv('ACCOUNTS_ADMIN_PASSWORD', None) or get_api_password()
        # test if we can connect to the Keycloak server
        dummy_client = self.get_admin_client()

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
                server_url=get_server_url(),
                username=self.user,
                password=self.passwd,
                realm_name=get_auth_realm(),
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
                get_server_url(), "realms", get_auth_realm())

            KEY = json.loads(requests.get(AUTH_PUBLIC_KEY_URL,
                                          verify=False).text)['public_key']
            cls.__public_key = b"-----BEGIN PUBLIC KEY-----\n" + \
                str.encode(KEY) + b"\n-----END PUBLIC KEY-----"
        return cls.__public_key

    @classmethod
    def decode_token(cls, token, audience="web-client"):
        """
        Check and retrieve authentication information from custom bearer token.
        Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
        'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

        :param token Token provided by Authorization header
        :type token: str
        :return: Decoded token information or None if token is invalid
        :rtype: dict | None
        """
        try:
            decoded = jwt.decode(token, cls.get_public_key(),
                                 algorithms='RS256', audience=audience)
        except jwt.exceptions.InvalidTokenError as e:
            raise InvalidToken(e) from e
        return decoded

    @with_refreshtoken
    def get_client(self, client_name):
        """
        Return the KC client

        ClientRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_clientrepresentation

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
    def get_group(self, group_id, with_members=False, with_details=False) -> UserGroup:
        """
        Return the group in the application realm

        :param group_id: the group id to get
        :param with_members: Default False, when set to True all members of the group are also retrieved
        :param with_details: Default False, when set to True all attributes of the group are also retrieved


        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :param with_members: If set the members (users) of the group are added to the group. Defaults to False
        :return: GroupRepresentation + UserRepresentation
        """
        admin_client = self.get_admin_client()
        group = admin_client.get_group(group_id)
        if with_members:
            members = admin_client.get_group_members(group_id)
            for user in members:
                user.update(
                    {'userGroups': admin_client.get_user_groups(user['id'], brief_representation=not with_details)})
                user.update(
                    {'realmRoles': admin_client.get_realm_roles_of_user(user['id'])})
            group.update({'members': members})
        return UserGroup.from_dict(group)

    @with_refreshtoken
    def get_groups(self, with_members=False) -> List[UserGroup]:
        """
        Return a list of all groups in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :param with_members: If set the members (users) of the group(s) are added to the group. Defaults to False
        :return: List(GroupRepresentation)
        """
        admin_client = self.get_admin_client()
        return [
            UserGroup.from_dict(self.get_group(group['id'], with_members))
            for group in admin_client.get_groups()
        ]

    @with_refreshtoken
    def create_group(self, name: str, parent: str = None) -> UserGroup:
        """
        Create a group in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :param name: the name of the group
        :param parent: parent group's id. Required to create a sub-group.
        """
        admin_client = self.get_admin_client()
        return UserGroup.from_dict(admin_client.create_group(
            payload={
                "name": name,
            },
            parent=parent,
            skip_exists=True))

    @with_refreshtoken
    def add_group(self, group: UserGroup, parent: str) -> UserGroup:
        """
        Create a group in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :param name: the name of the group
        :param parent: parent group's id. Required to create a sub-group.
        :return: UserGroup
        """
        admin_client = self.get_admin_client()
        return UserGroup.from_dict(admin_client.create_group(
            payload=group.to_dict(),
            parent=parent,
            skip_exists=True))

    @with_refreshtoken
    def update_group(self, group_id: str, name: str) -> UserGroup:
        """
        Updates the group identified by the given group_id in the application realm

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :param group_id: the id of the group to update
        :param name: the new name of the group
        """
        admin_client = self.get_admin_client()
        return UserGroup.from_dict(admin_client.update_group(
            group_id=group_id,
            payload={
                "name": name
            }))

    @with_refreshtoken
    def group_user_add(self, user_id, group_id):
        """
        Add user to group (user_id and group_id)

        :param user_id:  id of user
        :param group_id:  id of group to add to
        :return: Keycloak server response
        """
        admin_client = self.get_admin_client()
        return admin_client.group_user_add(user_id, group_id)

    @with_refreshtoken
    def group_user_remove(self, user_id, group_id):
        """
        Remove user from group (user_id and group_id)

        :param user_id:  id of user
        :param group_id:  id of group to remove from
        :return: Keycloak server response
        """
        admin_client = self.get_admin_client()
        return admin_client.group_user_remove(user_id, group_id)

    @with_refreshtoken
    def get_users(self, query=None, with_details=False) -> List[User]:
        """
        Return a list of all users in the application realm

        :param query: Default None, the query filter for getting the users
        :param with_details: Default False, when set to True all attributes of the group are also retrieved

        UserRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :param query: query filtering the users see https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_users_resource
        :return: List(UserRepresentation + GroupRepresentation)
        """
        admin_client = self.get_admin_client()
        users = []
        for user in admin_client.get_users(query=query):
            user.update({
                "userGroups": admin_client.get_user_groups(user['id'], brief_representation=not with_details),
                'realmRoles': admin_client.get_realm_roles_of_user(user['id'])
            })
            users.append(User.from_dict(user))
        return users

    @with_refreshtoken
    def get_user(self, user_id, with_details=False) -> User:
        """
        Get the user including the user groups

        :param user_id_or_username: User id or username
        :param with_details: Default False, when set to True all attributes of the group are also retrieved


        UserRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :return: UserRepresentation + GroupRepresentation
        """
        admin_client = self.get_admin_client()
        if is_uuid(user_id):
            try:
                user = admin_client.get_user(user_id)
            except KeycloakGetError as e:
                raise UserNotFound(user_id)
            except InvalidToken as e:
                raise UserNotFound(user_id)

        else:
            found_users = admin_client.get_users({"username": user_id, "exact": True})
            if len(found_users) == 0:
                raise UserNotFound(user_id)
            try:
                user = admin_client.get_user(found_users[0]['id'])  # Load full data
            except KeycloakGetError as e:
                raise UserNotFound(user_id)
            except InvalidToken as e:
                raise UserNotFound(user_id)

        user.update({
            "userGroups": admin_client.get_user_groups(user_id=user['id'], brief_representation=not with_details),
            'realmRoles': admin_client.get_realm_roles_of_user(user['id'])
        })
        return User.from_dict(user)

    def get_current_user(self) -> User:
        """
        Get the current user including the user groups

        UserRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_userrepresentation

        GroupRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_grouprepresentation

        :return: UserRepresentation + GroupRepresentation
        """
        return self.get_user(self._get_keycloak_user_id())

    @with_refreshtoken
    def get_user_realm_roles(self, user_id) -> List[str]:
        """
        Get the user realm roles within the current realm

        :param user_id: User id

        RoleRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_rolerepresentation

        :return: (array RoleRepresentation)
        """
        admin_client = self.get_admin_client()
        return admin_client.get_realm_roles_of_user(user_id)

    def get_current_user_realm_roles(self) -> List[str]:
        """
        Get the current user realm roles within the current realm

        RoleRepresentation
        https://www.keycloak.org/docs-api/16.0/rest-api/index.html#_rolerepresentation

        :return: (array RoleRepresentation)
        """
        return self.get_user_realm_roles(self._get_keycloak_user_id())

    @with_refreshtoken
    def get_user_client_roles(self, user_id, client_name) -> List[str]:
        """
        Get the user including the user resource access

        :param user_id: User id
        :param client_name: Client name
        :return: (array RoleRepresentation)
        """
        admin_client = self.get_admin_client()
        client_id = admin_client.get_client_id(client_name)
        return admin_client.get_client_roles_of_user(user_id, client_id)

    def get_current_user_client_roles(self, client_name) -> List[str]:
        """
        Get the user including the user resource access

        :param client_name: Client name
        :return: UserRepresentation + GroupRepresentation
        """
        cur_user_id = self._get_keycloak_user_id()
        return self.get_user_client_roles(cur_user_id, client_name)

    def user_has_client_role(self, user_id, client_name, role) -> bool:
        """
        Tests if the user has the given role within the given client

        :param user_id: User id
        :param client_name: Name of the client
        :param role: Name of the role
        """
        roles = [user_client_role for user_client_role in self.get_user_client_roles(
            user_id, client_name) if user_client_role['name'] == role]
        return roles != []

    def user_has_realm_role(self, user_id, role) -> bool:
        """
        Tests if the user has the given role within the current realm

        :param user_id: User id
        :param role: Name of the role
        """
        roles = [user_realm_role for user_realm_role in self.get_user_realm_roles(
            user_id) if user_realm_role['name'] == role]
        return roles != []

    def current_user_has_client_role(self, client_name, role) -> bool:
        """
        Tests if the current user has the given role within the given client

        :param client_name: Name of the client
        :param role: Name of the role
        """
        return self.user_has_client_role(
            self._get_keycloak_user_id(),
            client_name,
            role)

    def current_user_has_realm_role(self, role) -> bool:
        """
        Tests if the current user has the given role within the current realm

        :param role: Name of the role
        """
        return self.user_has_realm_role(
            self._get_keycloak_user_id(),
            role)

    @with_refreshtoken
    def get_client_role_members(self, client_name, role) -> List[User]:
        """
        Get all users for the specified client and role

        :param client_name: Client name
        :param role: Role name
        """
        admin_client = self.get_admin_client()
        client_id = admin_client.get_client_id(client_name)
        return [User.from_dict(u) for u in admin_client.get_client_role_members(client_id, role)]

    @with_refreshtoken
    def user_add_update_attribute(self, user_id, attribute_name, attribute_value):
        """
        Adds or when exists updates the attribute to/of the User with the attribute value

        param user_id: id of the user
        param attribute_name: name of the attribute to add/update
        param attribute_value: value of the attribute

        """
        admin_client = self.get_admin_client()
        user = self.get_user(user_id)
        attributes = user.get('attributes', {}) or {}
        attributes[attribute_name] = attribute_value
        admin_client.update_user(
            user_id,
            {
                'attributes': attributes
            })

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
