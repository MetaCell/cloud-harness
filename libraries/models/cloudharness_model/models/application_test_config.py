# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.api_tests_config import ApiTestsConfig
from cloudharness_model.models.e2_e_tests_config import E2ETestsConfig
from cloudharness_model.models.unit_tests_config import UnitTestsConfig
from cloudharness_model import util

from cloudharness_model.models.api_tests_config import ApiTestsConfig  # noqa: E501
from cloudharness_model.models.e2_e_tests_config import E2ETestsConfig  # noqa: E501
from cloudharness_model.models.unit_tests_config import UnitTestsConfig  # noqa: E501

class ApplicationTestConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, unit=None, api=None, e2e=None):  # noqa: E501
        """ApplicationTestConfig - a model defined in OpenAPI

        :param unit: The unit of this ApplicationTestConfig.  # noqa: E501
        :type unit: UnitTestsConfig
        :param api: The api of this ApplicationTestConfig.  # noqa: E501
        :type api: ApiTestsConfig
        :param e2e: The e2e of this ApplicationTestConfig.  # noqa: E501
        :type e2e: E2ETestsConfig
        """
        self.openapi_types = {
            'unit': UnitTestsConfig,
            'api': ApiTestsConfig,
            'e2e': E2ETestsConfig
        }

        self.attribute_map = {
            'unit': 'unit',
            'api': 'api',
            'e2e': 'e2e'
        }

        self._unit = unit
        self._api = api
        self._e2e = e2e

    @classmethod
    def from_dict(cls, dikt) -> 'ApplicationTestConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ApplicationTestConfig of this ApplicationTestConfig.  # noqa: E501
        :rtype: ApplicationTestConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def unit(self):
        """Gets the unit of this ApplicationTestConfig.


        :return: The unit of this ApplicationTestConfig.
        :rtype: UnitTestsConfig
        """
        return self._unit

    @unit.setter
    def unit(self, unit):
        """Sets the unit of this ApplicationTestConfig.


        :param unit: The unit of this ApplicationTestConfig.
        :type unit: UnitTestsConfig
        """
        if unit is None:
            raise ValueError("Invalid value for `unit`, must not be `None`")  # noqa: E501

        self._unit = unit

    @property
    def api(self):
        """Gets the api of this ApplicationTestConfig.


        :return: The api of this ApplicationTestConfig.
        :rtype: ApiTestsConfig
        """
        return self._api

    @api.setter
    def api(self, api):
        """Sets the api of this ApplicationTestConfig.


        :param api: The api of this ApplicationTestConfig.
        :type api: ApiTestsConfig
        """
        if api is None:
            raise ValueError("Invalid value for `api`, must not be `None`")  # noqa: E501

        self._api = api

    @property
    def e2e(self):
        """Gets the e2e of this ApplicationTestConfig.


        :return: The e2e of this ApplicationTestConfig.
        :rtype: E2ETestsConfig
        """
        return self._e2e

    @e2e.setter
    def e2e(self, e2e):
        """Sets the e2e of this ApplicationTestConfig.


        :param e2e: The e2e of this ApplicationTestConfig.
        :type e2e: E2ETestsConfig
        """
        if e2e is None:
            raise ValueError("Invalid value for `e2e`, must not be `None`")  # noqa: E501

        self._e2e = e2e