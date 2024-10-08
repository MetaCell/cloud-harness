# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from workflows_api.models.operation import Operation  # noqa: E501
from workflows_api.models.operation_search_result import OperationSearchResult  # noqa: E501
from workflows_api.models.operation_status import OperationStatus  # noqa: E501
from workflows_api.test import BaseTestCase


class TestCreateAndAccessController(BaseTestCase):
    """CreateAndAccessController integration test stubs"""

    def test_delete_operation(self):
        """Test case for delete_operation

        deletes operation by name
        """
        headers = {
        }
        response = self.client.open(
            '/operations/{name}'.format(name='name_example'),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_operation(self):
        """Test case for get_operation

        get operation by name
        """
        headers = {
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/operations/{name}'.format(name='name_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_operations(self):
        """Test case for list_operations

        lists operations
        """
        query_string = [('status', QUEUED),
                        ('previous_search_token', 'previous_search_token_example'),
                        ('limit', 10)]
        headers = {
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/operations',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_log_operation(self):
        """Test case for log_operation

        get operation by name
        """
        headers = {
            'Accept': 'text/plain',
        }
        response = self.client.open(
            '/operations/{name}/logs'.format(name='name_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
