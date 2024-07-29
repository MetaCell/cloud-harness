from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model import Model
from cloudharness_model import util


class ApiTestsConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, enabled=None, autotest=None, run_params=None, checks=None):  # noqa: E501
        """ApiTestsConfig - a model defined in OpenAPI

        :param enabled: The enabled of this ApiTestsConfig.  # noqa: E501
        :type enabled: bool
        :param autotest: The autotest of this ApiTestsConfig.  # noqa: E501
        :type autotest: bool
        :param run_params: The run_params of this ApiTestsConfig.  # noqa: E501
        :type run_params: List[str]
        :param checks: The checks of this ApiTestsConfig.  # noqa: E501
        :type checks: List[str]
        """
        self.openapi_types = {
            'enabled': bool,
            'autotest': bool,
            'run_params': List[str],
            'checks': List[str]
        }

        self.attribute_map = {
            'enabled': 'enabled',
            'autotest': 'autotest',
            'run_params': 'runParams',
            'checks': 'checks'
        }

        self._enabled = enabled
        self._autotest = autotest
        self._run_params = run_params
        self._checks = checks

    @classmethod
    def from_dict(cls, dikt) -> 'ApiTestsConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ApiTestsConfig of this ApiTestsConfig.  # noqa: E501
        :rtype: ApiTestsConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def enabled(self) -> bool:
        """Gets the enabled of this ApiTestsConfig.

        Enables api tests for this application (default: false)  # noqa: E501

        :return: The enabled of this ApiTestsConfig.
        :rtype: bool
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool):
        """Sets the enabled of this ApiTestsConfig.

        Enables api tests for this application (default: false)  # noqa: E501

        :param enabled: The enabled of this ApiTestsConfig.
        :type enabled: bool
        """
        if enabled is None:
            raise ValueError("Invalid value for `enabled`, must not be `None`")  # noqa: E501

        self._enabled = enabled

    @property
    def autotest(self) -> bool:
        """Gets the autotest of this ApiTestsConfig.

        Specify whether to run the common smoke tests  # noqa: E501

        :return: The autotest of this ApiTestsConfig.
        :rtype: bool
        """
        return self._autotest

    @autotest.setter
    def autotest(self, autotest: bool):
        """Sets the autotest of this ApiTestsConfig.

        Specify whether to run the common smoke tests  # noqa: E501

        :param autotest: The autotest of this ApiTestsConfig.
        :type autotest: bool
        """
        if autotest is None:
            raise ValueError("Invalid value for `autotest`, must not be `None`")  # noqa: E501

        self._autotest = autotest

    @property
    def run_params(self) -> List[str]:
        """Gets the run_params of this ApiTestsConfig.

        Additional schemathesis parameters  # noqa: E501

        :return: The run_params of this ApiTestsConfig.
        :rtype: List[str]
        """
        return self._run_params

    @run_params.setter
    def run_params(self, run_params: List[str]):
        """Sets the run_params of this ApiTestsConfig.

        Additional schemathesis parameters  # noqa: E501

        :param run_params: The run_params of this ApiTestsConfig.
        :type run_params: List[str]
        """

        self._run_params = run_params

    @property
    def checks(self) -> List[str]:
        """Gets the checks of this ApiTestsConfig.

        One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers.  # noqa: E501

        :return: The checks of this ApiTestsConfig.
        :rtype: List[str]
        """
        return self._checks

    @checks.setter
    def checks(self, checks: List[str]):
        """Sets the checks of this ApiTestsConfig.

        One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers.  # noqa: E501

        :param checks: The checks of this ApiTestsConfig.
        :type checks: List[str]
        """
        if checks is None:
            raise ValueError("Invalid value for `checks`, must not be `None`")  # noqa: E501

        self._checks = checks
