# coding: utf-8

"""
    CloudHarness Sample API

    CloudHarness Sample api

    The version of the OpenAPI document: 0.1.0
    Contact: cloudharness@metacell.us
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from cloudharness_cli.samples.api.workflows_api import WorkflowsApi


class TestWorkflowsApi(unittest.TestCase):
    """WorkflowsApi unit test stubs"""

    def setUp(self) -> None:
        self.api = WorkflowsApi()

    def tearDown(self) -> None:
        pass

    def test_submit_async(self) -> None:
        """Test case for submit_async

        Send an asynchronous operation
        """
        pass

    def test_submit_sync(self) -> None:
        """Test case for submit_sync

        Send a synchronous operation
        """
        pass

    def test_submit_sync_with_results(self) -> None:
        """Test case for submit_sync_with_results

        Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
        """
        pass


if __name__ == '__main__':
    unittest.main()
