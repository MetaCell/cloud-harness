# coding: utf-8

"""
    Volumes manager API

    CloudHarness Volumes manager API  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Generated by: https://openapi-generator.tech
"""

from cloudharness_cli.volumemanager.paths.pvc_name.get import PvcNameGet
from cloudharness_cli.volumemanager.paths.pvc.post import PvcPost


class RestApi(
    PvcNameGet,
    PvcPost,
):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """
    pass
