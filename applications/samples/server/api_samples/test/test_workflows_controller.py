# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from api_samples.models.inline_response202 import InlineResponse202  # noqa: E501
from api_samples.test import BaseTestCase


class TestWorkflowsController(BaseTestCase):
    """WorkflowsController integration test stubs"""

    def test_operation_submit_async(self):
        """Test case for operation_submit_async

        Send an asyncronous operation
        """
        response = self.client.open(
            '/0.1.0/operation_async',
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_operation_submit_sync(self):
        """Test case for operation_submit_sync

        Send a syncronous operation
        """
        response = self.client.open(
            '/0.1.0/operation_sync',
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
