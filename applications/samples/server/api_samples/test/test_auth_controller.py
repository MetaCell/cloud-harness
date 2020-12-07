# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from api_samples.models.valid import Valid  # noqa: E501
from api_samples.test import BaseTestCase


class TestAuthController(BaseTestCase):
    """AuthController integration test stubs"""

    def test_valid_token(self):
        """Test case for valid_token

        Check if the token is valid
        """
        response = self.client.open(
            '/0.1.0/valid',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
