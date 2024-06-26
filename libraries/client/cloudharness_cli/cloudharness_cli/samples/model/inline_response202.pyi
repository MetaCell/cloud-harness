# coding: utf-8

"""
    CloudHarness Sample API

    CloudHarness Sample api  # noqa: E501

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

from cloudharness_cli.samples import schemas  # noqa: F401


class InlineResponse202(
    schemas.DictSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        
        class properties:
        
            @staticmethod
            def task() -> typing.Type['InlineResponse202Task']:
                return InlineResponse202Task
            __annotations__ = {
                "task": task,
            }
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["task"]) -> 'InlineResponse202Task': ...
    
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    
    def __getitem__(self, name: typing.Union[typing_extensions.Literal["task", ], str]):
        # dict_instance[name] accessor
        return super().__getitem__(name)
    
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["task"]) -> typing.Union['InlineResponse202Task', schemas.Unset]: ...
    
    @typing.overload
    def get_item_oapg(self, name: str) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    
    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["task", ], str]):
        return super().get_item_oapg(name)
    

    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, ],
        task: typing.Union['InlineResponse202Task', schemas.Unset] = schemas.unset,
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[schemas.AnyTypeSchema, dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, None, list, tuple, bytes],
    ) -> 'InlineResponse202':
        return super().__new__(
            cls,
            *args,
            task=task,
            _configuration=_configuration,
            **kwargs,
        )

from cloudharness_cli/samples.model.inline_response202_task import InlineResponse202Task
