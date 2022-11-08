# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from cloudharness_cli.samples.apis.path_to_api import path_to_api

import enum


class PathValues(str, enum.Enum):
    ERROR = "/error"
    PING = "/ping"
    VALID = "/valid"
    VALIDCOOKIE = "/valid-cookie"
    SAMPLERESOURCES = "/sampleresources"
    SAMPLERESOURCES_SAMPLERESOURCE_ID = "/sampleresources/{sampleresourceId}"
    OPERATION_ASYNC = "/operation_async"
    OPERATION_SYNC = "/operation_sync"
    OPERATION_SYNC_RESULTS = "/operation_sync_results"
