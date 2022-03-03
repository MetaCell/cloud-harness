# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model import util


class RegistryConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name=None, secret=None):  # noqa: E501
        """RegistryConfig - a model defined in OpenAPI

        :param name: The name of this RegistryConfig.  # noqa: E501
        :type name: str
        :param secret: The secret of this RegistryConfig.  # noqa: E501
        :type secret: str
        """
        self.openapi_types = {
            'name': str,
            'secret': str
        }

        self.attribute_map = {
            'name': 'name',
            'secret': 'secret'
        }

        self._name = name
        self._secret = secret

    @classmethod
    def from_dict(cls, dikt) -> 'RegistryConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The RegistryConfig of this RegistryConfig.  # noqa: E501
        :rtype: RegistryConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this RegistryConfig.


        :return: The name of this RegistryConfig.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this RegistryConfig.


        :param name: The name of this RegistryConfig.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def secret(self):
        """Gets the secret of this RegistryConfig.

        Optional secret used for pulling from docker registry.  # noqa: E501

        :return: The secret of this RegistryConfig.
        :rtype: str
        """
        return self._secret

    @secret.setter
    def secret(self, secret):
        """Sets the secret of this RegistryConfig.

        Optional secret used for pulling from docker registry.  # noqa: E501

        :param secret: The secret of this RegistryConfig.
        :type secret: str
        """

        self._secret = secret
