# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from cloudharness_cli.workflows.paths.operations_name import Api

from cloudharness_cli.workflows.paths import PathValues

path = PathValues.OPERATIONS_NAME