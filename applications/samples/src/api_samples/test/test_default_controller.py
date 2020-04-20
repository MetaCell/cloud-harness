# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from api_samples.models.valid import Valid  # noqa: E501
from api_samples.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_operation_sync_post(self):
        """Test case for operation_sync_post

        Send a syncronous operation
        """
        response = self.client.open(
            '0.1.0/operation-sync',
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_valid_token(self):
        """Test case for valid_token

        Check if the token is valid
        """
        response = self.client.open(
            '0.1.0/valid',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
