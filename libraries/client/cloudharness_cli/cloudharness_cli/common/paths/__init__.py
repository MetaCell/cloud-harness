# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from cloudharness_cli.common.apis.path_to_api import path_to_api

import enum


class PathValues(str, enum.Enum):
    SENTRY_GETDSN_APPNAME = "/sentry/getdsn/{appname}"
    ACCOUNTS_CONFIG = "/accounts/config"
