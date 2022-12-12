import typing_extensions

from cloudharness_cli.workflows.apis.tags import TagValues
from cloudharness_cli.workflows.apis.tags.create_and_access_api import CreateAndAccessApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.CREATE_AND_ACCESS: CreateAndAccessApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.CREATE_AND_ACCESS: CreateAndAccessApi,
    }
)
