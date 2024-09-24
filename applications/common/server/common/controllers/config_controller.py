
import connexion
import six
from typing import Dict
from typing import Tuple
from typing import Union

from common.models.app_version import AppVersion  # noqa: E501
from common import util

from cloudharness.utils.config import CloudharnessConfig
from cloudharness_model.models import HarnessMainConfig


def get_version():  # noqa: E501
    """get_version

     # noqa: E501


    :rtype: Union[AppVersion, Tuple[AppVersion, int], Tuple[AppVersion, int, Dict[str, str]]
    """

    config: HarnessMainConfig = HarnessMainConfig.from_dict(CloudharnessConfig.get_configuration())

    return AppVersion(tag=config.tag, build=config.build_hash)
