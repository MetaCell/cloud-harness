# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model import util


class NameValue(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name=None, value=None):  # noqa: E501
        """NameValue - a model defined in OpenAPI

        :param name: The name of this NameValue.  # noqa: E501
        :type name: str
        :param value: The value of this NameValue.  # noqa: E501
        :type value: str
        """
        self.openapi_types = {
            'name': str,
            'value': str
        }

        self.attribute_map = {
            'name': 'name',
            'value': 'value'
        }

        self._name = name
        self._value = value

    @classmethod
    def from_dict(cls, dikt) -> 'NameValue':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The NameValue of this NameValue.  # noqa: E501
        :rtype: NameValue
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this NameValue.


        :return: The name of this NameValue.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this NameValue.


        :param name: The name of this NameValue.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def value(self):
        """Gets the value of this NameValue.


        :return: The value of this NameValue.
        :rtype: str
        """
        return self._value

    @value.setter
    def value(self, value):
        """Sets the value of this NameValue.


        :param value: The value of this NameValue.
        :type value: str
        """

        self._value = value