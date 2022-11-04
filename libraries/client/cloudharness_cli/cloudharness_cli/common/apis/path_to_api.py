import typing_extensions

from cloudharness_cli.common.paths import PathValues
from cloudharness_cli.common.apis.paths.sentry_getdsn_appname import SentryGetdsnAppname
from cloudharness_cli.common.apis.paths.accounts_config import AccountsConfig

PathToApi = typing_extensions.TypedDict(
    'PathToApi',
    {
        PathValues.SENTRY_GETDSN_APPNAME: SentryGetdsnAppname,
        PathValues.ACCOUNTS_CONFIG: AccountsConfig,
    }
)

path_to_api = PathToApi(
    {
        PathValues.SENTRY_GETDSN_APPNAME: SentryGetdsnAppname,
        PathValues.ACCOUNTS_CONFIG: AccountsConfig,
    }
)
