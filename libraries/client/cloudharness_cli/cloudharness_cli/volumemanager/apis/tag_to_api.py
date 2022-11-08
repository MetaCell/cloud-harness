import typing_extensions

from cloudharness_cli.volumemanager.apis.tags import TagValues
from cloudharness_cli.volumemanager.apis.tags.rest_api import RestApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.REST: RestApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.REST: RestApi,
    }
)
