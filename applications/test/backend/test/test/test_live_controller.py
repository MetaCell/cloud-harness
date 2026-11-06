import unittest

from flask import json

from test.test import BaseTestCase


class TestLiveController(BaseTestCase):
    """LiveController integration test stubs"""

    def test_live(self):
        """Test case for live

        Test if application is healthy
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/live',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
