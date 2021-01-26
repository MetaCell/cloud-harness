# coding: utf-8

"""
    CH common service API

    Cloud Harness Platform - Reference CH service API  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest

import cloudharness_cli.common
from cloudharness_cli.common.api.sentry_api import SentryApi  # noqa: E501
from cloudharness_cli.common.rest import ApiException


class TestSentryApi(unittest.TestCase):
    """SentryApi unit test stubs"""

    def setUp(self):
        self.api = cloudharness_cli.common.api.sentry_api.SentryApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_getdsn(self):
        """Test case for getdsn

        Gets the Sentry DSN for a given application  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()