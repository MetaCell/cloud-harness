# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from notifications.test import BaseTestCase


class TestTestController(BaseTestCase):
    """TestController integration test stubs"""

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
