import typing_extensions

from cloudharness_cli.workflows.paths import PathValues
from cloudharness_cli.workflows.apis.paths.operations import Operations
from cloudharness_cli.workflows.apis.paths.operations_name import OperationsName
from cloudharness_cli.workflows.apis.paths.operations_name_logs import OperationsNameLogs

PathToApi = typing_extensions.TypedDict(
    'PathToApi',
    {
        PathValues.OPERATIONS: Operations,
        PathValues.OPERATIONS_NAME: OperationsName,
        PathValues.OPERATIONS_NAME_LOGS: OperationsNameLogs,
    }
)

path_to_api = PathToApi(
    {
        PathValues.OPERATIONS: Operations,
        PathValues.OPERATIONS_NAME: OperationsName,
        PathValues.OPERATIONS_NAME_LOGS: OperationsNameLogs,
    }
)
