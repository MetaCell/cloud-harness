# coding: utf-8

"""
    CH common service API

    Cloud Harness Platform - Reference CH service API

    The version of the OpenAPI document: 0.1.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from cloudharness_cli.common.models.app_version import AppVersion

class TestAppVersion(unittest.TestCase):
    """AppVersion unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> AppVersion:
        """Test AppVersion
            include_optional is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `AppVersion`
        """
        model = AppVersion()
        if include_optional:
            return AppVersion(
                build = '',
                tag = ''
            )
        else:
            return AppVersion(
        )
        """

    def testAppVersion(self):
        """Test AppVersion"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()