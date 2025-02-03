# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from common.test import BaseTestCase


class TestSentryController(BaseTestCase):
    """SentryController integration test stubs"""

    def test_getdsn(self):
        """Test case for getdsn

        Gets the Sentry DSN for a given application
        """
        headers = {
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/sentry/getdsn/{appname}'.format(appname='appname_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
