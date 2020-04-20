import connexion
import six

from workflows_api.models.operation import Operation  # noqa: E501
from workflows_api.models.operation_search_result import OperationSearchResult  # noqa: E501
from workflows_api.models.operation_status import OperationStatus  # noqa: E501
from workflows_api import util


def delete_operation(name):  # noqa: E501
    """deletes operation by name

    delete operation by its name  # noqa: E501

    :param name: 
    :type name: str

    :rtype: None
    """
    return 'do some magic!'


def get_operation(name):  # noqa: E501
    """get operation by name

    retrieves an operation by its name  # noqa: E501

    :param name: 
    :type name: str

    :rtype: List[Operation]
    """
    return 'do some magic!'


def list_operations(status=None, previous_search_token=None, limit=None):  # noqa: E501
    """lists operations

    see all operations for the user  # noqa: E501

    :param status: filter by status
    :type status: dict | bytes
    :param previous_search_token: continue previous search (pagination chunks)
    :type previous_search_token: str
    :param limit: maximum number of records to return per page
    :type limit: int

    :rtype: OperationSearchResult
    """
    if connexion.request.is_json:
        status =  OperationStatus.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def log_operation(name):  # noqa: E501
    """get operation by name

    retrieves an operation log by its name  # noqa: E501

    :param name: 
    :type name: str

    :rtype: str
    """
    return 'do some magic!'
