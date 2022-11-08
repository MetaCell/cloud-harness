# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from common.models.base_model_ import Model
from common import util


class InlineResponse200(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, url=None, realm=None, client_id=None):  # noqa: E501
        """InlineResponse200 - a model defined in OpenAPI

        :param url: The url of this InlineResponse200.  # noqa: E501
        :type url: str
        :param realm: The realm of this InlineResponse200.  # noqa: E501
        :type realm: str
        :param client_id: The client_id of this InlineResponse200.  # noqa: E501
        :type client_id: str
        """
        self.openapi_types = {
            'url': str,
            'realm': str,
            'client_id': str
        }

        self.attribute_map = {
            'url': 'url',
            'realm': 'realm',
            'client_id': 'clientId'
        }

        self._url = url
        self._realm = realm
        self._client_id = client_id

    @classmethod
    def from_dict(cls, dikt) -> 'InlineResponse200':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The inline_response_200 of this InlineResponse200.  # noqa: E501
        :rtype: InlineResponse200
        """
        return util.deserialize_model(dikt, cls)

    @property
    def url(self):
        """Gets the url of this InlineResponse200.

        The auth URL.  # noqa: E501

        :return: The url of this InlineResponse200.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this InlineResponse200.

        The auth URL.  # noqa: E501

        :param url: The url of this InlineResponse200.
        :type url: str
        """

        self._url = url

    @property
    def realm(self):
        """Gets the realm of this InlineResponse200.

        The realm.  # noqa: E501

        :return: The realm of this InlineResponse200.
        :rtype: str
        """
        return self._realm

    @realm.setter
    def realm(self, realm):
        """Sets the realm of this InlineResponse200.

        The realm.  # noqa: E501

        :param realm: The realm of this InlineResponse200.
        :type realm: str
        """

        self._realm = realm

    @property
    def client_id(self):
        """Gets the client_id of this InlineResponse200.

        The clientID.  # noqa: E501

        :return: The client_id of this InlineResponse200.
        :rtype: str
        """
        return self._client_id

    @client_id.setter
    def client_id(self, client_id):
        """Sets the client_id of this InlineResponse200.

        The clientID.  # noqa: E501

        :param client_id: The client_id of this InlineResponse200.
        :type client_id: str
        """

        self._client_id = client_id
