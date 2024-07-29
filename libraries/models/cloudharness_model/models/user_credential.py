from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model import Model
from cloudharness_model import util


class UserCredential(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, created_date=None, credential_data=None, id=None, priority=None, secret_data=None, temporary=None, type=None, user_label=None, value=None):  # noqa: E501
        """UserCredential - a model defined in OpenAPI

        :param created_date: The created_date of this UserCredential.  # noqa: E501
        :type created_date: int
        :param credential_data: The credential_data of this UserCredential.  # noqa: E501
        :type credential_data: str
        :param id: The id of this UserCredential.  # noqa: E501
        :type id: str
        :param priority: The priority of this UserCredential.  # noqa: E501
        :type priority: int
        :param secret_data: The secret_data of this UserCredential.  # noqa: E501
        :type secret_data: str
        :param temporary: The temporary of this UserCredential.  # noqa: E501
        :type temporary: bool
        :param type: The type of this UserCredential.  # noqa: E501
        :type type: str
        :param user_label: The user_label of this UserCredential.  # noqa: E501
        :type user_label: str
        :param value: The value of this UserCredential.  # noqa: E501
        :type value: str
        """
        self.openapi_types = {
            'created_date': int,
            'credential_data': str,
            'id': str,
            'priority': int,
            'secret_data': str,
            'temporary': bool,
            'type': str,
            'user_label': str,
            'value': str
        }

        self.attribute_map = {
            'created_date': 'createdDate',
            'credential_data': 'credentialData',
            'id': 'id',
            'priority': 'priority',
            'secret_data': 'secretData',
            'temporary': 'temporary',
            'type': 'type',
            'user_label': 'userLabel',
            'value': 'value'
        }

        self._created_date = created_date
        self._credential_data = credential_data
        self._id = id
        self._priority = priority
        self._secret_data = secret_data
        self._temporary = temporary
        self._type = type
        self._user_label = user_label
        self._value = value

    @classmethod
    def from_dict(cls, dikt) -> 'UserCredential':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The UserCredential of this UserCredential.  # noqa: E501
        :rtype: UserCredential
        """
        return util.deserialize_model(dikt, cls)

    @property
    def created_date(self) -> int:
        """Gets the created_date of this UserCredential.


        :return: The created_date of this UserCredential.
        :rtype: int
        """
        return self._created_date

    @created_date.setter
    def created_date(self, created_date: int):
        """Sets the created_date of this UserCredential.


        :param created_date: The created_date of this UserCredential.
        :type created_date: int
        """

        self._created_date = created_date

    @property
    def credential_data(self) -> str:
        """Gets the credential_data of this UserCredential.


        :return: The credential_data of this UserCredential.
        :rtype: str
        """
        return self._credential_data

    @credential_data.setter
    def credential_data(self, credential_data: str):
        """Sets the credential_data of this UserCredential.


        :param credential_data: The credential_data of this UserCredential.
        :type credential_data: str
        """

        self._credential_data = credential_data

    @property
    def id(self) -> str:
        """Gets the id of this UserCredential.


        :return: The id of this UserCredential.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this UserCredential.


        :param id: The id of this UserCredential.
        :type id: str
        """

        self._id = id

    @property
    def priority(self) -> int:
        """Gets the priority of this UserCredential.


        :return: The priority of this UserCredential.
        :rtype: int
        """
        return self._priority

    @priority.setter
    def priority(self, priority: int):
        """Sets the priority of this UserCredential.


        :param priority: The priority of this UserCredential.
        :type priority: int
        """

        self._priority = priority

    @property
    def secret_data(self) -> str:
        """Gets the secret_data of this UserCredential.


        :return: The secret_data of this UserCredential.
        :rtype: str
        """
        return self._secret_data

    @secret_data.setter
    def secret_data(self, secret_data: str):
        """Sets the secret_data of this UserCredential.


        :param secret_data: The secret_data of this UserCredential.
        :type secret_data: str
        """

        self._secret_data = secret_data

    @property
    def temporary(self) -> bool:
        """Gets the temporary of this UserCredential.


        :return: The temporary of this UserCredential.
        :rtype: bool
        """
        return self._temporary

    @temporary.setter
    def temporary(self, temporary: bool):
        """Sets the temporary of this UserCredential.


        :param temporary: The temporary of this UserCredential.
        :type temporary: bool
        """

        self._temporary = temporary

    @property
    def type(self) -> str:
        """Gets the type of this UserCredential.


        :return: The type of this UserCredential.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this UserCredential.


        :param type: The type of this UserCredential.
        :type type: str
        """

        self._type = type

    @property
    def user_label(self) -> str:
        """Gets the user_label of this UserCredential.


        :return: The user_label of this UserCredential.
        :rtype: str
        """
        return self._user_label

    @user_label.setter
    def user_label(self, user_label: str):
        """Sets the user_label of this UserCredential.


        :param user_label: The user_label of this UserCredential.
        :type user_label: str
        """

        self._user_label = user_label

    @property
    def value(self) -> str:
        """Gets the value of this UserCredential.


        :return: The value of this UserCredential.
        :rtype: str
        """
        return self._value

    @value.setter
    def value(self, value: str):
        """Sets the value of this UserCredential.


        :param value: The value of this UserCredential.
        :type value: str
        """

        self._value = value
