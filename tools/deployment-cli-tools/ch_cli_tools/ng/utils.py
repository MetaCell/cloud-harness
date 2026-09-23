from typing import TYPE_CHECKING

from cloudharness.utils import dict_merge  # type: ignore

if TYPE_CHECKING:
    from .model import CHValues


def merge_with_layer(base: "CHValues", layer: "CHValues"):

    if base is layer or layer.env is None:
        return base.all_raw_values() if base.exists() else {}
    match base.exists(), layer.exists():
        case True, True:
            return dict_merge(base.all_raw_values(), layer.all_raw_values())
        case False, True:
            return layer.all_raw_values()
        case True, False:
            return base.all_raw_values()
        case False, False:
            return {}
