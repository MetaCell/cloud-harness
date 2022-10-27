"""
Access workflows using Argo REST API
Reference: https://argoproj.github.io/docs/argo/docs/rest-api.html
https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md
"""

import yaml

from argo_workflows import ApiClient, Configuration

from argo_workflows.api.workflow_service_api import WorkflowServiceApi,\
    IoArgoprojWorkflowV1alpha1WorkflowCreateRequest as V1alpha1WorkflowCreateRequest,\
    IoArgoprojWorkflowV1alpha1WorkflowList as V1alpha1WorkflowList,\
    IoArgoprojWorkflowV1alpha1Workflow as V1alpha1Workflow, IoArgoprojWorkflowV1alpha1WorkflowSubmitRequest, 


# determine the namespace of the current app and run the workflow in that namespace
from cloudharness.utils.config import CloudharnessConfig as conf
from cloudharness import log, applications

ch_conf = conf.get_configuration()
namespace = conf.get_namespace()


class WorkflowException(Exception):
    def __init__(self, status, message=''):
        super().__init__(message)
        self.status = status


class WorkflowNotFound(WorkflowException):
    def __init__(self):
        super().__init__(404)


class BadParam(WorkflowException):
    def __init__(self, param_name, message=''):
        super().__init__(400, message)
        self.param = param_name


class ArgoObject:

    @classmethod
    def from_spec(cls):
        pass

    def spec(self):
        raise NotImplemented


# --- Wrapper objects for api results ---

class Phase:
    Pending = "Pending"
    Running = "Running"
    Succeeded = "Succeeded"
    Skipped = "Skipped"
    Failed = "Failed"
    Error = "Error"

    # Legacy names (deprecated)
    NodeRunning = Running
    NodePending = Pending
    NodeSucceeded = Succeeded
    NodeSkipped = Skipped
    NodeFailed = Failed
    NodeError = Error

    @classmethod
    def phases(cls):
        return (cls.Pending, cls.Running, cls.Succeeded, cls.Skipped, cls.Failed, cls.Error)


class Workflow:
    def __init__(self, api_workflow: V1alpha1Workflow):
        self.name = api_workflow.metadata.name
        self.status = api_workflow.status.phase if api_workflow.status else None
        self.create_time = api_workflow.metadata.creation_timestamp
        self.raw = api_workflow

    def is_finished(self):
        return self.status in (Phase.Error, Phase.Succeeded, Phase.Skipped, Phase.Failed)

    def __str__(self):
        return yaml.dump(self.raw)

    def succeeded(self):
        return self.status == Phase.Succeeded

    def failed(self):
        return self.status == Phase.Failed

    def get_status_message(self):
        return self.raw.status.message

    @property
    def pod_names(self):
        return [node.id for node in self.raw.status.nodes.values() if not node.children]


class SearchResult:
    def __init__(self, raw_dict):
        self.items = tuple(Workflow(
            item) for item in raw_dict.items) if raw_dict.items is not None else []
        self.continue_token = raw_dict.metadata._continue
        self.raw = raw_dict

    def __str__(self):
        return self.raw

    def __repr__(self):
        return str(self.raw)


# --- Api functions ---    `

def get_api_client():
    configuration = get_configuration()

    # configuration.api_key['authorization'] = 'YOUR_API_KEY' # TODO verify if we need an api key
    api_instance = ApiClient(configuration)
    return api_instance


def get_configuration():
    if not conf.is_test():
        host = applications.get_configuration('argo').get_service_address()
    else:
        host = applications.get_configuration('argo').get_public_address()
    return Configuration(host=host)


def get_workflows(status=None, limit=10, continue_token=None, timeout_seconds=3, field_selector=None, fields=None, **kwargs) -> SearchResult:
    """https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#list_namespaced_custom_object"""
    # Notice: field selector doesn't work though advertised, except fot metadata.name and metadata.namespace https://github.com/kubernetes/kubernetes/issues/51046
    # The filtering by phase can be obtained through labels: https://github.com/argoproj/argo/issues/496
    service = WorkflowServiceApi(api_client=get_api_client())

    try:
        api_response = service.list_workflows(namespace, list_options_limit=limit, list_options_continue=continue_token,
                                              list_options_label_selector=f"workflows.argoproj.io/phase={status}" if status else None,
                                              _request_timeout=timeout_seconds,
                                              list_options_field_selector=field_selector, fields=fields, **kwargs)

    except ValueError:
        # Exception is raised when no results are found
        return V1alpha1WorkflowList(items=[], metadata={})
    else:
        return SearchResult(api_response)


def submit_workflow(spec) -> Workflow:
    log.debug(f"Submitting workflow %s", spec)

    service = WorkflowServiceApi(api_client=get_api_client())

    req = IoArgoprojWorkflowV1alpha1WorkflowSubmitRequest(
        workflow=spec, instance_id=namespace, namespace=namespace)

    # pprint(service.list_workflows('ch', V1alpha1WorkflowList()))
    wf = service.submit_workflow(namespace, req)
    return Workflow(wf)


def delete_workflow(workflow_name):
    service = WorkflowServiceApi(api_client=get_api_client())
    try:
        service.delete_workflow(namespace, workflow_name,
                                delete_options_grace_period_seconds=0)
    except Exception as e:
        if e.status == 404:
            raise WorkflowNotFound()
        raise WorkflowException("Workflow delete error") from e


def get_workflow(workflow_name) -> Workflow:
    service = WorkflowServiceApi(api_client=get_api_client())
    try:
        api_response = service.get_workflow(namespace, name=workflow_name)
    except Exception as e:
        if e.status == 404:
            raise WorkflowNotFound()
        raise WorkflowException("Workflow get error") from e
    workflow = Workflow(api_response)
    if workflow.failed():
        raise WorkflowException("Workflow failed: " +
                                workflow.get_status_message())

    return workflow


def get_workflow_logs(workflow_name) -> str:
    return '\n'.join(get_workflow_logs_list(workflow_name))


def get_workflow_logs_list(workflow_name):
    from ..infrastructure import k8s

    workflow = get_workflow(workflow_name)
    pod_names = workflow.pod_names
    if len(pod_names) == 0:
        return ''
    return [k8s.get_pod_logs(pod_name) for pod_name in pod_names]


if __name__ == '__main__':
    from pprint import pprint
    conf.get_configuration()['test'] = True
    res = get_workflows()
    pprint(res)
    # pprint(get_workflow('hello-world-sfzd4'))
