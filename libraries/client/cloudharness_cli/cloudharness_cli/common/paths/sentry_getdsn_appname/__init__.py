# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from cloudharness_cli.common.paths.sentry_getdsn_appname import Api

from cloudharness_cli.common.paths import PathValues

path = PathValues.SENTRY_GETDSN_APPNAME