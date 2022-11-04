import typing_extensions

from cloudharness_cli.samples.apis.tags import TagValues
from cloudharness_cli.samples.apis.tags.auth_api import AuthApi
from cloudharness_cli.samples.apis.tags.workflows_api import WorkflowsApi
from cloudharness_cli.samples.apis.tags.resource_api import ResourceApi
from cloudharness_cli.samples.apis.tags.test_api import TestApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.AUTH: AuthApi,
        TagValues.WORKFLOWS: WorkflowsApi,
        TagValues.RESOURCE: ResourceApi,
        TagValues.TEST: TestApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.AUTH: AuthApi,
        TagValues.WORKFLOWS: WorkflowsApi,
        TagValues.RESOURCE: ResourceApi,
        TagValues.TEST: TestApi,
    }
)
