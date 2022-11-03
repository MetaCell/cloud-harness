# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from cloudharness_cli.common.paths.accounts_config import Api

from cloudharness_cli.common.paths import PathValues

path = PathValues.ACCOUNTS_CONFIG