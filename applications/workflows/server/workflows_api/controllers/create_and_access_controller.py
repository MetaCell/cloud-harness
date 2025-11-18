import connexion
import six

from workflows_api.models.operation import Operation  # noqa: E501
from workflows_api.models.operation_search_result import OperationSearchResult  # noqa: E501
from workflows_api.models.operation_status import OperationStatus  # noqa: E501
from workflows_api.models.search_result_data import SearchResultData  # noqa: E501
from workflows_api import util

from workflows_api.service import workflow_service
from workflows_api.service.workflow_service import OperationNotFound, OperationException, BadParam

from cloudharness import log


def delete_operation(name):  # noqa: E501
    """deletes operation by name

    delete operation by its name  # noqa: E501

    :param name: 
    :type name: str

    :rtype: None
    """
    try:
        workflow_service.delete_operation(name)
    except OperationNotFound as e:
        return (f'{name} not found', 404)
    except OperationException as e:
        log.error(f'Unhandled remote exception while deleting workflow {name}', exc_info=e)
        return f'Unexpected error', e.status


def get_operation(name):  # noqa: E501
    """get operation by name

    retrieves an operation by its name  # noqa: E501

    :param name: 
    :type name: str

    :rtype: List[Operation]
    """
    try:
        return workflow_service.get_operation(name)
    except OperationNotFound as e:
        return (f'{name} not found', 404)
    except OperationException as e:
        log.error(f'Unhandled remote exception while retrieving workflow {name}', exc_info=e)
        return f'Unexpected error', e.status


def list_operations(status=None, previous_search_token=None, limit=None):  # noqa: E501
    """lists operations

    see all operations for the user  # noqa: E501

    :param status: filter by status
    :type status: dict | bytes
    :param previous_search: continue previous search (pagination chunks)
    :type previous_search: dict | bytes
    :param limit: maximum number of records to return per page
    :type limit: int

    :rtype: OperationSearchResult
    """
    try:
        return workflow_service.list_operations(status, continue_token=previous_search_token, limit=limit)
    except BadParam as e:
        return (f'Bad parameter: {e.param}, {e}', e.status)
    except OperationException as e:
        log.error(f'Unhandled remote exception while retrieving workflows', exc_info=e)
        return f'{e}', e.status


def log_operation(name):  # noqa: E501
    """get operation by name

    retrieves an operation log by its name  # noqa: E501

    :param name: 
    :type name: str

    :rtype: str
    """
    if not name or name == '':
        return ''
    try:
        return workflow_service.log_operation(name)
    except OperationNotFound as e:
        return (f'{name} not found', 404)
