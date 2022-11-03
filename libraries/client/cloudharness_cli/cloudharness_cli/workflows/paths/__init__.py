# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from cloudharness_cli.workflows.apis.path_to_api import path_to_api

import enum


class PathValues(str, enum.Enum):
    OPERATIONS = "/operations"
    OPERATIONS_NAME = "/operations/{name}"
    OPERATIONS_NAME_LOGS = "/operations/{name}/logs"
