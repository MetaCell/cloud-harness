# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from samples.models.inline_response202 import InlineResponse202  # noqa: E501
from samples.test import BaseTestCase


class TestWorkflowsController(BaseTestCase):
    """WorkflowsController integration test stubs"""

    def test_submit_async(self):
        """Test case for submit_async

        Send an asynchronous operation
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/operation_async',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_submit_sync(self):
        """Test case for submit_sync

        Send a synchronous operation
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/operation_sync',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_submit_sync_with_results(self):
        """Test case for submit_sync_with_results

        Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
        """
        query_string = [('a', 10),
                        ('b', 10)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/operation_sync_results',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
