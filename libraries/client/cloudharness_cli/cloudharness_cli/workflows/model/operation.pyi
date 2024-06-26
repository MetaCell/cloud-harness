# coding: utf-8

"""
    Workflows API

    Workflows API  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Contact: cloudharness@metacell.us
    Generated by: https://openapi-generator.tech
"""

from datetime import date, datetime  # noqa: F401
import decimal  # noqa: F401
import functools  # noqa: F401
import io  # noqa: F401
import re  # noqa: F401
import typing  # noqa: F401
import typing_extensions  # noqa: F401
import uuid  # noqa: F401

import frozendict  # noqa: F401

from cloudharness_cli.workflows import schemas  # noqa: F401


class Operation(
    schemas.AnyTypeSchema,
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.

    represents the status of a distributed API call
    """


    class MetaOapg:
        
        class properties:
            message = schemas.StrSchema
            name = schemas.StrSchema
            createTime = schemas.DateTimeSchema
        
            @staticmethod
            def status() -> typing.Type['OperationStatus']:
                return OperationStatus
            workflow = schemas.StrSchema
            __annotations__ = {
                "message": message,
                "name": name,
                "createTime": createTime,
                "status": status,
                "workflow": workflow,
            }

    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["message"]) -> MetaOapg.properties.message: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["name"]) -> MetaOapg.properties.name: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["createTime"]) -> MetaOapg.properties.createTime: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["status"]) -> 'OperationStatus': ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["workflow"]) -> MetaOapg.properties.workflow: ...
    
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    
    def __getitem__(self, name: typing.Union[typing_extensions.Literal["message", "name", "createTime", "status", "workflow", ], str]):
        # dict_instance[name] accessor
        return super().__getitem__(name)
    
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["message"]) -> typing.Union[MetaOapg.properties.message, schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["name"]) -> typing.Union[MetaOapg.properties.name, schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["createTime"]) -> typing.Union[MetaOapg.properties.createTime, schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["status"]) -> typing.Union['OperationStatus', schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["workflow"]) -> typing.Union[MetaOapg.properties.workflow, schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: str) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    
    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["message", "name", "createTime", "status", "workflow", ], str]):
        return super().get_item_oapg(name)
    

    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, bool, None, list, tuple, bytes, io.FileIO, io.BufferedReader, ],
        message: typing.Union[MetaOapg.properties.message, str, schemas.Unset] = schemas.unset,
        name: typing.Union[MetaOapg.properties.name, str, schemas.Unset] = schemas.unset,
        createTime: typing.Union[MetaOapg.properties.createTime, str, datetime, schemas.Unset] = schemas.unset,
        status: typing.Union['OperationStatus', schemas.Unset] = schemas.unset,
        workflow: typing.Union[MetaOapg.properties.workflow, str, schemas.Unset] = schemas.unset,
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[schemas.AnyTypeSchema, dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, None, list, tuple, bytes],
    ) -> 'Operation':
        return super().__new__(
            cls,
            *args,
            message=message,
            name=name,
            createTime=createTime,
            status=status,
            workflow=workflow,
            _configuration=_configuration,
            **kwargs,
        )

from cloudharness_cli/workflows.model.operation_status import OperationStatus
