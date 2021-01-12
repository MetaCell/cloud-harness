# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from cloudharness_cli.samples.models.valid import Valid  # noqa: E501
from cloudharness_cli.samples.test import BaseTestCase


class TestAuthController(BaseTestCase):
    """AuthController integration test stubs"""

    def test_valid_token(self):
        """Test case for valid_token

        Check if the token is valid. Get a token by logging into the base url
        """
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/valid',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
