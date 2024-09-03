from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model import util


class GitDependencyConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, url=None, branch_tag=None, path=None):  # noqa: E501
        """GitDependencyConfig - a model defined in OpenAPI

        :param url: The url of this GitDependencyConfig.  # noqa: E501
        :type url: str
        :param branch_tag: The branch_tag of this GitDependencyConfig.  # noqa: E501
        :type branch_tag: str
        :param path: The path of this GitDependencyConfig.  # noqa: E501
        :type path: str
        """
        self.openapi_types = {
            'url': str,
            'branch_tag': str,
            'path': str
        }

        self.attribute_map = {
            'url': 'url',
            'branch_tag': 'branch_tag',
            'path': 'path'
        }

        self._url = url
        self._branch_tag = branch_tag
        self._path = path

    @classmethod
    def from_dict(cls, dikt) -> 'GitDependencyConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The GitDependencyConfig of this GitDependencyConfig.  # noqa: E501
        :rtype: GitDependencyConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def url(self) -> str:
        """Gets the url of this GitDependencyConfig.


        :return: The url of this GitDependencyConfig.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url: str):
        """Sets the url of this GitDependencyConfig.


        :param url: The url of this GitDependencyConfig.
        :type url: str
        """
        if url is None:
            raise ValueError("Invalid value for `url`, must not be `None`")  # noqa: E501

        self._url = url

    @property
    def branch_tag(self) -> str:
        """Gets the branch_tag of this GitDependencyConfig.


        :return: The branch_tag of this GitDependencyConfig.
        :rtype: str
        """
        return self._branch_tag

    @branch_tag.setter
    def branch_tag(self, branch_tag: str):
        """Sets the branch_tag of this GitDependencyConfig.


        :param branch_tag: The branch_tag of this GitDependencyConfig.
        :type branch_tag: str
        """
        if branch_tag is None:
            raise ValueError("Invalid value for `branch_tag`, must not be `None`")  # noqa: E501

        self._branch_tag = branch_tag

    @property
    def path(self) -> str:
        """Gets the path of this GitDependencyConfig.

        Defines the path where the repo is cloned. default: /git  # noqa: E501

        :return: The path of this GitDependencyConfig.
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path: str):
        """Sets the path of this GitDependencyConfig.

        Defines the path where the repo is cloned. default: /git  # noqa: E501

        :param path: The path of this GitDependencyConfig.
        :type path: str
        """

        self._path = path
