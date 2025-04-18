from cloudharness.workflows import argo_service
from workflows_api.models import OperationSearchResult, Operation, SearchResultData

OperationNotFound = argo_service.WorkflowNotFound
OperationException = argo_service.WorkflowException
BadParam = argo_service.BadParam


def argo_workflow_to_operation(workflow: argo_service.Workflow):
    return Operation(name=workflow.name,
                     status=workflow.status,
                     create_time=workflow.create_time,
                     workflow=workflow.raw.to_str())


def delete_operation(name):
    """deletes operation by id"""
    argo_service.delete_workflow(name)


def get_operation(name):
    """get operation by id"""
    return argo_workflow_to_operation(argo_service.get_workflow(name))


def list_operations(status=None, continue_token=None, limit=None) -> OperationSearchResult:
    """lists operations

    see all operations for the user

    :param status: filter by status
    :type status: dict | bytes
    :param previous_search: continue previous search (pagination chunks)
    :type previous_search: dict | bytes
    :param limit: maximum number of records to return per page
    :type limit: int

    :rtype: OperationSearchResult
    """

    argo_raw_result = argo_service.get_workflows(status, limit=limit, continue_token=continue_token)
    result = OperationSearchResult()
    result.items = tuple(argo_workflow_to_operation(item) for item in argo_raw_result.items)
    result.meta = SearchResultData(continue_token=argo_raw_result.continue_token)
    return result


def log_operation(name: str) -> str:
    """get operation logs
    :param name: workflow name
    :rtype: str
    """

    return argo_service.get_workflow_logs(name)
