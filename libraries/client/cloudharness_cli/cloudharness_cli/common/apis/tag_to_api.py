import typing_extensions

from cloudharness_cli.common.apis.tags import TagValues
from cloudharness_cli.common.apis.tags.sentry_api import SentryApi
from cloudharness_cli.common.apis.tags.accounts_api import AccountsApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.SENTRY: SentryApi,
        TagValues.ACCOUNTS: AccountsApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.SENTRY: SentryApi,
        TagValues.ACCOUNTS: AccountsApi,
    }
)
