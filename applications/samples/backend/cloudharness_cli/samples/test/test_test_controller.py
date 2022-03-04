# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from cloudharness_cli.samples.test import BaseTestCase


class TestTestController(BaseTestCase):
    """TestController integration test stubs"""

    def test_error(self):
        """Test case for error

        test sentry is working
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/error',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_ping(self):
        """Test case for ping

        test the application is up
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/ping',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
