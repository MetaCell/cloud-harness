# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.user import User
from cloudharness_model import util

from cloudharness_model.models.user import User  # noqa: E501

class CDCEventMeta(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, app_name=None, user=None, args=None, kwargs=None, description=None):  # noqa: E501
        """CDCEventMeta - a model defined in OpenAPI

        :param app_name: The app_name of this CDCEventMeta.  # noqa: E501
        :type app_name: str
        :param user: The user of this CDCEventMeta.  # noqa: E501
        :type user: User
        :param args: The args of this CDCEventMeta.  # noqa: E501
        :type args: List[Dict]
        :param kwargs: The kwargs of this CDCEventMeta.  # noqa: E501
        :type kwargs: object
        :param description: The description of this CDCEventMeta.  # noqa: E501
        :type description: str
        """
        self.openapi_types = {
            'app_name': str,
            'user': User,
            'args': List[Dict],
            'kwargs': object,
            'description': str
        }

        self.attribute_map = {
            'app_name': 'app_name',
            'user': 'user',
            'args': 'args',
            'kwargs': 'kwargs',
            'description': 'description'
        }

        self._app_name = app_name
        self._user = user
        self._args = args
        self._kwargs = kwargs
        self._description = description

    @classmethod
    def from_dict(cls, dikt) -> 'CDCEventMeta':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The CDCEventMeta of this CDCEventMeta.  # noqa: E501
        :rtype: CDCEventMeta
        """
        return util.deserialize_model(dikt, cls)

    @property
    def app_name(self):
        """Gets the app_name of this CDCEventMeta.

        The name of the application/microservice sending the message  # noqa: E501

        :return: The app_name of this CDCEventMeta.
        :rtype: str
        """
        return self._app_name

    @app_name.setter
    def app_name(self, app_name):
        """Sets the app_name of this CDCEventMeta.

        The name of the application/microservice sending the message  # noqa: E501

        :param app_name: The app_name of this CDCEventMeta.
        :type app_name: str
        """
        if app_name is None:
            raise ValueError("Invalid value for `app_name`, must not be `None`")  # noqa: E501

        self._app_name = app_name

    @property
    def user(self):
        """Gets the user of this CDCEventMeta.


        :return: The user of this CDCEventMeta.
        :rtype: User
        """
        return self._user

    @user.setter
    def user(self, user):
        """Sets the user of this CDCEventMeta.


        :param user: The user of this CDCEventMeta.
        :type user: User
        """

        self._user = user

    @property
    def args(self):
        """Gets the args of this CDCEventMeta.

        the caller function arguments  # noqa: E501

        :return: The args of this CDCEventMeta.
        :rtype: List[Dict]
        """
        return self._args

    @args.setter
    def args(self, args):
        """Sets the args of this CDCEventMeta.

        the caller function arguments  # noqa: E501

        :param args: The args of this CDCEventMeta.
        :type args: List[Dict]
        """

        self._args = args

    @property
    def kwargs(self):
        """Gets the kwargs of this CDCEventMeta.

        the caller function keyword arguments  # noqa: E501

        :return: The kwargs of this CDCEventMeta.
        :rtype: object
        """
        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        """Sets the kwargs of this CDCEventMeta.

        the caller function keyword arguments  # noqa: E501

        :param kwargs: The kwargs of this CDCEventMeta.
        :type kwargs: object
        """

        self._kwargs = kwargs

    @property
    def description(self):
        """Gets the description of this CDCEventMeta.

        General description -- for human consumption  # noqa: E501

        :return: The description of this CDCEventMeta.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this CDCEventMeta.

        General description -- for human consumption  # noqa: E501

        :param description: The description of this CDCEventMeta.
        :type description: str
        """

        self._description = description