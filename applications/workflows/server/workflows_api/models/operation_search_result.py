# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from workflows_api.models.base_model_ import Model
from workflows_api.models.operation import Operation
from workflows_api.models.search_result_data import SearchResultData
from workflows_api import util

from workflows_api.models.operation import Operation  # noqa: E501
from workflows_api.models.search_result_data import SearchResultData  # noqa: E501

class OperationSearchResult(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, meta=None, items=None):  # noqa: E501
        """OperationSearchResult - a model defined in OpenAPI

        :param meta: The meta of this OperationSearchResult.  # noqa: E501
        :type meta: SearchResultData
        :param items: The items of this OperationSearchResult.  # noqa: E501
        :type items: List[Operation]
        """
        self.openapi_types = {
            'meta': SearchResultData,
            'items': List[Operation]
        }

        self.attribute_map = {
            'meta': 'meta',
            'items': 'items'
        }

        self._meta = meta
        self._items = items

    @classmethod
    def from_dict(cls, dikt) -> 'OperationSearchResult':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The OperationSearchResult of this OperationSearchResult.  # noqa: E501
        :rtype: OperationSearchResult
        """
        return util.deserialize_model(dikt, cls)

    @property
    def meta(self):
        """Gets the meta of this OperationSearchResult.


        :return: The meta of this OperationSearchResult.
        :rtype: SearchResultData
        """
        return self._meta

    @meta.setter
    def meta(self, meta):
        """Sets the meta of this OperationSearchResult.


        :param meta: The meta of this OperationSearchResult.
        :type meta: SearchResultData
        """

        self._meta = meta

    @property
    def items(self):
        """Gets the items of this OperationSearchResult.


        :return: The items of this OperationSearchResult.
        :rtype: List[Operation]
        """
        return self._items

    @items.setter
    def items(self, items):
        """Sets the items of this OperationSearchResult.


        :param items: The items of this OperationSearchResult.
        :type items: List[Operation]
        """

        self._items = items
