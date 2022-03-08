# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.user_credential import UserCredential
from cloudharness_model import util

from cloudharness_model.models.user_credential import UserCredential  # noqa: E501

class User(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, access=None, attributes=None, client_roles=None, created_timestamp=None, credentials=None, disableable_credential_types=None, email=None, email_verified=None, enabled=None, federation_link=None, first_name=None, groups=None, id=None, last_name=None, realm_roles=None, required_actions=None, service_account_client_id=None, username=None, additional_properties=None):  # noqa: E501
        """User - a model defined in OpenAPI

        :param access: The access of this User.  # noqa: E501
        :type access: Dict[str, object]
        :param attributes: The attributes of this User.  # noqa: E501
        :type attributes: Dict[str, object]
        :param client_roles: The client_roles of this User.  # noqa: E501
        :type client_roles: Dict[str, object]
        :param created_timestamp: The created_timestamp of this User.  # noqa: E501
        :type created_timestamp: int
        :param credentials: The credentials of this User.  # noqa: E501
        :type credentials: List[UserCredential]
        :param disableable_credential_types: The disableable_credential_types of this User.  # noqa: E501
        :type disableable_credential_types: List[str]
        :param email: The email of this User.  # noqa: E501
        :type email: str
        :param email_verified: The email_verified of this User.  # noqa: E501
        :type email_verified: bool
        :param enabled: The enabled of this User.  # noqa: E501
        :type enabled: bool
        :param federation_link: The federation_link of this User.  # noqa: E501
        :type federation_link: str
        :param first_name: The first_name of this User.  # noqa: E501
        :type first_name: str
        :param groups: The groups of this User.  # noqa: E501
        :type groups: List[str]
        :param id: The id of this User.  # noqa: E501
        :type id: str
        :param last_name: The last_name of this User.  # noqa: E501
        :type last_name: str
        :param realm_roles: The realm_roles of this User.  # noqa: E501
        :type realm_roles: List[str]
        :param required_actions: The required_actions of this User.  # noqa: E501
        :type required_actions: List[str]
        :param service_account_client_id: The service_account_client_id of this User.  # noqa: E501
        :type service_account_client_id: str
        :param username: The username of this User.  # noqa: E501
        :type username: str
        :param additional_properties: The additional_properties of this User.  # noqa: E501
        :type additional_properties: object
        """
        self.openapi_types = {
            'access': Dict[str, object],
            'attributes': Dict[str, object],
            'client_roles': Dict[str, object],
            'created_timestamp': int,
            'credentials': List[UserCredential],
            'disableable_credential_types': List[str],
            'email': str,
            'email_verified': bool,
            'enabled': bool,
            'federation_link': str,
            'first_name': str,
            'groups': List[str],
            'id': str,
            'last_name': str,
            'realm_roles': List[str],
            'required_actions': List[str],
            'service_account_client_id': str,
            'username': str,
            'additional_properties': object
        }

        self.attribute_map = {
            'access': 'access',
            'attributes': 'attributes',
            'client_roles': 'clientRoles',
            'created_timestamp': 'createdTimestamp',
            'credentials': 'credentials',
            'disableable_credential_types': 'disableableCredentialTypes',
            'email': 'email',
            'email_verified': 'emailVerified',
            'enabled': 'enabled',
            'federation_link': 'federationLink',
            'first_name': 'firstName',
            'groups': 'groups',
            'id': 'id',
            'last_name': 'lastName',
            'realm_roles': 'realmRoles',
            'required_actions': 'requiredActions',
            'service_account_client_id': 'serviceAccountClientId',
            'username': 'username',
            'additional_properties': 'additionalProperties'
        }

        self._access = access
        self._attributes = attributes
        self._client_roles = client_roles
        self._created_timestamp = created_timestamp
        self._credentials = credentials
        self._disableable_credential_types = disableable_credential_types
        self._email = email
        self._email_verified = email_verified
        self._enabled = enabled
        self._federation_link = federation_link
        self._first_name = first_name
        self._groups = groups
        self._id = id
        self._last_name = last_name
        self._realm_roles = realm_roles
        self._required_actions = required_actions
        self._service_account_client_id = service_account_client_id
        self._username = username
        self._additional_properties = additional_properties

    @classmethod
    def from_dict(cls, dikt) -> 'User':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The User of this User.  # noqa: E501
        :rtype: User
        """
        return util.deserialize_model(dikt, cls)

    @property
    def access(self):
        """Gets the access of this User.


        :return: The access of this User.
        :rtype: Dict[str, object]
        """
        return self._access

    @access.setter
    def access(self, access):
        """Sets the access of this User.


        :param access: The access of this User.
        :type access: Dict[str, object]
        """

        self._access = access

    @property
    def attributes(self):
        """Gets the attributes of this User.


        :return: The attributes of this User.
        :rtype: Dict[str, object]
        """
        return self._attributes

    @attributes.setter
    def attributes(self, attributes):
        """Sets the attributes of this User.


        :param attributes: The attributes of this User.
        :type attributes: Dict[str, object]
        """

        self._attributes = attributes

    @property
    def client_roles(self):
        """Gets the client_roles of this User.


        :return: The client_roles of this User.
        :rtype: Dict[str, object]
        """
        return self._client_roles

    @client_roles.setter
    def client_roles(self, client_roles):
        """Sets the client_roles of this User.


        :param client_roles: The client_roles of this User.
        :type client_roles: Dict[str, object]
        """

        self._client_roles = client_roles

    @property
    def created_timestamp(self):
        """Gets the created_timestamp of this User.


        :return: The created_timestamp of this User.
        :rtype: int
        """
        return self._created_timestamp

    @created_timestamp.setter
    def created_timestamp(self, created_timestamp):
        """Sets the created_timestamp of this User.


        :param created_timestamp: The created_timestamp of this User.
        :type created_timestamp: int
        """

        self._created_timestamp = created_timestamp

    @property
    def credentials(self):
        """Gets the credentials of this User.


        :return: The credentials of this User.
        :rtype: List[UserCredential]
        """
        return self._credentials

    @credentials.setter
    def credentials(self, credentials):
        """Sets the credentials of this User.


        :param credentials: The credentials of this User.
        :type credentials: List[UserCredential]
        """

        self._credentials = credentials

    @property
    def disableable_credential_types(self):
        """Gets the disableable_credential_types of this User.


        :return: The disableable_credential_types of this User.
        :rtype: List[str]
        """
        return self._disableable_credential_types

    @disableable_credential_types.setter
    def disableable_credential_types(self, disableable_credential_types):
        """Sets the disableable_credential_types of this User.


        :param disableable_credential_types: The disableable_credential_types of this User.
        :type disableable_credential_types: List[str]
        """

        self._disableable_credential_types = disableable_credential_types

    @property
    def email(self):
        """Gets the email of this User.


        :return: The email of this User.
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, email):
        """Sets the email of this User.


        :param email: The email of this User.
        :type email: str
        """

        self._email = email

    @property
    def email_verified(self):
        """Gets the email_verified of this User.


        :return: The email_verified of this User.
        :rtype: bool
        """
        return self._email_verified

    @email_verified.setter
    def email_verified(self, email_verified):
        """Sets the email_verified of this User.


        :param email_verified: The email_verified of this User.
        :type email_verified: bool
        """

        self._email_verified = email_verified

    @property
    def enabled(self):
        """Gets the enabled of this User.


        :return: The enabled of this User.
        :rtype: bool
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        """Sets the enabled of this User.


        :param enabled: The enabled of this User.
        :type enabled: bool
        """

        self._enabled = enabled

    @property
    def federation_link(self):
        """Gets the federation_link of this User.


        :return: The federation_link of this User.
        :rtype: str
        """
        return self._federation_link

    @federation_link.setter
    def federation_link(self, federation_link):
        """Sets the federation_link of this User.


        :param federation_link: The federation_link of this User.
        :type federation_link: str
        """

        self._federation_link = federation_link

    @property
    def first_name(self):
        """Gets the first_name of this User.


        :return: The first_name of this User.
        :rtype: str
        """
        return self._first_name

    @first_name.setter
    def first_name(self, first_name):
        """Sets the first_name of this User.


        :param first_name: The first_name of this User.
        :type first_name: str
        """

        self._first_name = first_name

    @property
    def groups(self):
        """Gets the groups of this User.


        :return: The groups of this User.
        :rtype: List[str]
        """
        return self._groups

    @groups.setter
    def groups(self, groups):
        """Sets the groups of this User.


        :param groups: The groups of this User.
        :type groups: List[str]
        """

        self._groups = groups

    @property
    def id(self):
        """Gets the id of this User.


        :return: The id of this User.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this User.


        :param id: The id of this User.
        :type id: str
        """

        self._id = id

    @property
    def last_name(self):
        """Gets the last_name of this User.


        :return: The last_name of this User.
        :rtype: str
        """
        return self._last_name

    @last_name.setter
    def last_name(self, last_name):
        """Sets the last_name of this User.


        :param last_name: The last_name of this User.
        :type last_name: str
        """

        self._last_name = last_name

    @property
    def realm_roles(self):
        """Gets the realm_roles of this User.


        :return: The realm_roles of this User.
        :rtype: List[str]
        """
        return self._realm_roles

    @realm_roles.setter
    def realm_roles(self, realm_roles):
        """Sets the realm_roles of this User.


        :param realm_roles: The realm_roles of this User.
        :type realm_roles: List[str]
        """

        self._realm_roles = realm_roles

    @property
    def required_actions(self):
        """Gets the required_actions of this User.


        :return: The required_actions of this User.
        :rtype: List[str]
        """
        return self._required_actions

    @required_actions.setter
    def required_actions(self, required_actions):
        """Sets the required_actions of this User.


        :param required_actions: The required_actions of this User.
        :type required_actions: List[str]
        """

        self._required_actions = required_actions

    @property
    def service_account_client_id(self):
        """Gets the service_account_client_id of this User.


        :return: The service_account_client_id of this User.
        :rtype: str
        """
        return self._service_account_client_id

    @service_account_client_id.setter
    def service_account_client_id(self, service_account_client_id):
        """Sets the service_account_client_id of this User.


        :param service_account_client_id: The service_account_client_id of this User.
        :type service_account_client_id: str
        """

        self._service_account_client_id = service_account_client_id

    @property
    def username(self):
        """Gets the username of this User.


        :return: The username of this User.
        :rtype: str
        """
        return self._username

    @username.setter
    def username(self, username):
        """Sets the username of this User.


        :param username: The username of this User.
        :type username: str
        """

        self._username = username

    @property
    def additional_properties(self):
        """Gets the additional_properties of this User.


        :return: The additional_properties of this User.
        :rtype: object
        """
        return self._additional_properties

    @additional_properties.setter
    def additional_properties(self, additional_properties):
        """Sets the additional_properties of this User.


        :param additional_properties: The additional_properties of this User.
        :type additional_properties: object
        """

        self._additional_properties = additional_properties