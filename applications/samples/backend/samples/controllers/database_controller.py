import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from samples.models.get_db_connect_string200_response import GetDbConnectString200Response  # noqa: E501
from samples import util


def get_db_connect_string():  # noqa: E501
    """Get database connection string

    Returns the database connection string for the current application. # noqa: E501


    :rtype: Union[GetDbConnectString200Response, Tuple[GetDbConnectString200Response, int], Tuple[GetDbConnectString200Response, int, Dict[str, str]]
    """
    from cloudharness.applications import get_current_configuration
    config = get_current_configuration()
    return config.get_db_connection_string()
