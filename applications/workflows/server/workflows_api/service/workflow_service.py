from cloudharness.workflows import argo
from workflows_api.models import OperationSearchResult, Operation, SearchResultData

OperationNotFound = argo.WorkflowNotFound
OperationException = argo.WorkflowException
BadParam = argo.BadParam


def argo_workflow_to_operation(workflow: argo.Workflow):
    return Operation(name=workflow.name,
                     status=workflow.status,
                     create_time=workflow.create_time,
                     workflow=workflow.raw.to_str())


def delete_operation(name):
    """deletes operation by id"""
    argo.delete_workflow(name)


def get_operation(name):
    """get operation by id"""
    return argo_workflow_to_operation(argo.get_workflow(name))


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

    argo_raw_result = argo.get_workflows(status, limit=limit, continue_token=continue_token)
    result = OperationSearchResult()
    if argo_raw_result:
        result.items = tuple(argo_workflow_to_operation(item) for item in argo_raw_result.items)
        result.meta = SearchResultData(continue_token=argo_raw_result.continue_token)
    else:
        result.items = []
        result.meta = SearchResultData()

    return result


def log_operation(name: str) -> str:
    """get operation logs
    :param name: workflow name
    :rtype: str
    """
    return argo.get_workflow_logs(name)
