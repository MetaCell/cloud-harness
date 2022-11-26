# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model import util


class DeploymentVolumeSpec(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, mountpath=None, size=None, usenfs=None, auto=None, name=None):  # noqa: E501
        """DeploymentVolumeSpec - a model defined in OpenAPI

        :param mountpath: The mountpath of this DeploymentVolumeSpec.  # noqa: E501
        :type mountpath: str
        :param size: The size of this DeploymentVolumeSpec.  # noqa: E501
        :type size: object
        :param usenfs: The usenfs of this DeploymentVolumeSpec.  # noqa: E501
        :type usenfs: bool
        :param auto: The auto of this DeploymentVolumeSpec.  # noqa: E501
        :type auto: bool
        :param name: The name of this DeploymentVolumeSpec.  # noqa: E501
        :type name: str
        """
        self.openapi_types = {
            'mountpath': str,
            'size': object,
            'usenfs': bool,
            'auto': bool,
            'name': str
        }

        self.attribute_map = {
            'mountpath': 'mountpath',
            'size': 'size',
            'usenfs': 'usenfs',
            'auto': 'auto',
            'name': 'name'
        }

        self._mountpath = mountpath
        self._size = size
        self._usenfs = usenfs
        self._auto = auto
        self._name = name

    @classmethod
    def from_dict(cls, dikt) -> 'DeploymentVolumeSpec':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The DeploymentVolumeSpec of this DeploymentVolumeSpec.  # noqa: E501
        :rtype: DeploymentVolumeSpec
        """
        return util.deserialize_model(dikt, cls)

    @property
    def mountpath(self):
        """Gets the mountpath of this DeploymentVolumeSpec.

        The mount path for the volume  # noqa: E501

        :return: The mountpath of this DeploymentVolumeSpec.
        :rtype: str
        """
        return self._mountpath

    @mountpath.setter
    def mountpath(self, mountpath):
        """Sets the mountpath of this DeploymentVolumeSpec.

        The mount path for the volume  # noqa: E501

        :param mountpath: The mountpath of this DeploymentVolumeSpec.
        :type mountpath: str
        """
        if mountpath is None:
            raise ValueError("Invalid value for `mountpath`, must not be `None`")  # noqa: E501

        self._mountpath = mountpath

    @property
    def size(self):
        """Gets the size of this DeploymentVolumeSpec.

        The volume size.   E.g. 5Gi  # noqa: E501

        :return: The size of this DeploymentVolumeSpec.
        :rtype: object
        """
        return self._size

    @size.setter
    def size(self, size):
        """Sets the size of this DeploymentVolumeSpec.

        The volume size.   E.g. 5Gi  # noqa: E501

        :param size: The size of this DeploymentVolumeSpec.
        :type size: object
        """

        self._size = size

    @property
    def usenfs(self):
        """Gets the usenfs of this DeploymentVolumeSpec.

        Set to `true` to use the nfs on the created volume and mount as ReadWriteMany.  # noqa: E501

        :return: The usenfs of this DeploymentVolumeSpec.
        :rtype: bool
        """
        return self._usenfs

    @usenfs.setter
    def usenfs(self, usenfs):
        """Sets the usenfs of this DeploymentVolumeSpec.

        Set to `true` to use the nfs on the created volume and mount as ReadWriteMany.  # noqa: E501

        :param usenfs: The usenfs of this DeploymentVolumeSpec.
        :type usenfs: bool
        """

        self._usenfs = usenfs

    @property
    def auto(self):
        """Gets the auto of this DeploymentVolumeSpec.

        When true, enables automatic template  # noqa: E501

        :return: The auto of this DeploymentVolumeSpec.
        :rtype: bool
        """
        return self._auto

    @auto.setter
    def auto(self, auto):
        """Sets the auto of this DeploymentVolumeSpec.

        When true, enables automatic template  # noqa: E501

        :param auto: The auto of this DeploymentVolumeSpec.
        :type auto: bool
        """
        if auto is None:
            raise ValueError("Invalid value for `auto`, must not be `None`")  # noqa: E501

        self._auto = auto

    @property
    def name(self):
        """Gets the name of this DeploymentVolumeSpec.

          # noqa: E501

        :return: The name of this DeploymentVolumeSpec.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this DeploymentVolumeSpec.

          # noqa: E501

        :param name: The name of this DeploymentVolumeSpec.
        :type name: str
        """

        self._name = name