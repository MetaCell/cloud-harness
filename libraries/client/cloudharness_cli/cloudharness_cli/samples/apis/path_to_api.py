import typing_extensions

from cloudharness_cli.samples.paths import PathValues
from cloudharness_cli.samples.apis.paths.error import Error
from cloudharness_cli.samples.apis.paths.ping import Ping
from cloudharness_cli.samples.apis.paths.valid import Valid
from cloudharness_cli.samples.apis.paths.valid_cookie import ValidCookie
from cloudharness_cli.samples.apis.paths.sampleresources import Sampleresources
from cloudharness_cli.samples.apis.paths.sampleresources_sampleresource_id import SampleresourcesSampleresourceId
from cloudharness_cli.samples.apis.paths.operation_async import OperationAsync
from cloudharness_cli.samples.apis.paths.operation_sync import OperationSync
from cloudharness_cli.samples.apis.paths.operation_sync_results import OperationSyncResults

PathToApi = typing_extensions.TypedDict(
    'PathToApi',
    {
        PathValues.ERROR: Error,
        PathValues.PING: Ping,
        PathValues.VALID: Valid,
        PathValues.VALIDCOOKIE: ValidCookie,
        PathValues.SAMPLERESOURCES: Sampleresources,
        PathValues.SAMPLERESOURCES_SAMPLERESOURCE_ID: SampleresourcesSampleresourceId,
        PathValues.OPERATION_ASYNC: OperationAsync,
        PathValues.OPERATION_SYNC: OperationSync,
        PathValues.OPERATION_SYNC_RESULTS: OperationSyncResults,
    }
)

path_to_api = PathToApi(
    {
        PathValues.ERROR: Error,
        PathValues.PING: Ping,
        PathValues.VALID: Valid,
        PathValues.VALIDCOOKIE: ValidCookie,
        PathValues.SAMPLERESOURCES: Sampleresources,
        PathValues.SAMPLERESOURCES_SAMPLERESOURCE_ID: SampleresourcesSampleresourceId,
        PathValues.OPERATION_ASYNC: OperationAsync,
        PathValues.OPERATION_SYNC: OperationSync,
        PathValues.OPERATION_SYNC_RESULTS: OperationSyncResults,
    }
)
