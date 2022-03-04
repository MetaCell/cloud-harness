# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
import re
from cloudharness_model import util

import re  # noqa: E501

class FileResourcesConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name=None, src=None, dst=None):  # noqa: E501
        """FileResourcesConfig - a model defined in OpenAPI

        :param name: The name of this FileResourcesConfig.  # noqa: E501
        :type name: str
        :param src: The src of this FileResourcesConfig.  # noqa: E501
        :type src: str
        :param dst: The dst of this FileResourcesConfig.  # noqa: E501
        :type dst: str
        """
        self.openapi_types = {
            'name': str,
            'src': str,
            'dst': str
        }

        self.attribute_map = {
            'name': 'name',
            'src': 'src',
            'dst': 'dst'
        }

        self._name = name
        self._src = src
        self._dst = dst

    @classmethod
    def from_dict(cls, dikt) -> 'FileResourcesConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FileResourcesConfig of this FileResourcesConfig.  # noqa: E501
        :rtype: FileResourcesConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this FileResourcesConfig.


        :return: The name of this FileResourcesConfig.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this FileResourcesConfig.


        :param name: The name of this FileResourcesConfig.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501
        if name is not None and not re.search(r'^[^<>:;,?*|]+$', name):  # noqa: E501
            raise ValueError("Invalid value for `name`, must be a follow pattern or equal to `/^[^<>:;,?*|]+$/`")  # noqa: E501

        self._name = name

    @property
    def src(self):
        """Gets the src of this FileResourcesConfig.


        :return: The src of this FileResourcesConfig.
        :rtype: str
        """
        return self._src

    @src.setter
    def src(self, src):
        """Sets the src of this FileResourcesConfig.


        :param src: The src of this FileResourcesConfig.
        :type src: str
        """
        if src is None:
            raise ValueError("Invalid value for `src`, must not be `None`")  # noqa: E501
        if src is not None and not re.search(r'^[^<>:;,?*|]+$', src):  # noqa: E501
            raise ValueError("Invalid value for `src`, must be a follow pattern or equal to `/^[^<>:;,?*|]+$/`")  # noqa: E501

        self._src = src

    @property
    def dst(self):
        """Gets the dst of this FileResourcesConfig.


        :return: The dst of this FileResourcesConfig.
        :rtype: str
        """
        return self._dst

    @dst.setter
    def dst(self, dst):
        """Sets the dst of this FileResourcesConfig.


        :param dst: The dst of this FileResourcesConfig.
        :type dst: str
        """
        if dst is None:
            raise ValueError("Invalid value for `dst`, must not be `None`")  # noqa: E501

        self._dst = dst