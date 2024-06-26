# coding: utf-8

"""
    CloudHarness Sample API

    CloudHarness Sample api  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Contact: cloudharness@metacell.us
    Generated by: https://openapi-generator.tech
"""

from cloudharness_cli.samples.paths.operation_async.get import SubmitAsync
from cloudharness_cli.samples.paths.operation_sync.get import SubmitSync
from cloudharness_cli.samples.paths.operation_sync_results.get import SubmitSyncWithResults


class WorkflowsApi(
    SubmitAsync,
    SubmitSync,
    SubmitSyncWithResults,
):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """
    pass
