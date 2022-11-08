import typing_extensions

from cloudharness_cli.volumemanager.paths import PathValues
from cloudharness_cli.volumemanager.apis.paths.pvc import Pvc
from cloudharness_cli.volumemanager.apis.paths.pvc_name import PvcName

PathToApi = typing_extensions.TypedDict(
    'PathToApi',
    {
        PathValues.PVC: Pvc,
        PathValues.PVC_NAME: PvcName,
    }
)

path_to_api = PathToApi(
    {
        PathValues.PVC: Pvc,
        PathValues.PVC_NAME: PvcName,
    }
)
