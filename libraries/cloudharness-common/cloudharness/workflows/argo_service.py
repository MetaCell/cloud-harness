"""
Access workflows using Argo REST API
Reference: https://argoproj.github.io/docs/argo/docs/rest-api.html
https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md
"""

import json

import yaml

from argo_workflows import ApiClient as ArgoApiClient, Configuration, exceptions
from argo_workflows.model_utils import ModelNormal
from argo_workflows.api.workflow_service_api import WorkflowServiceApi
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_create_request import IoArgoprojWorkflowV1alpha1WorkflowCreateRequest as V1alpha1WorkflowCreateRequest
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow import IoArgoprojWorkflowV1alpha1Workflow as V1alpha1Workflow
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_list import IoArgoprojWorkflowV1alpha1WorkflowList as V1alpha1WorkflowList


# determine the namespace of the current app and run the workflow in that namespace
from cloudharness.utils.config import CloudharnessConfig as conf
from cloudharness import log, applications

ch_conf = conf.get_configuration()
try:
    namespace = conf.get_namespace()
except Exception as e:
    log.error("Error getting namespace: %s", e)
    namespace = 'default'


class ApiClient(ArgoApiClient):
    """Keep the existing optional-field contract with the generated SDK models."""

    @staticmethod
    def _response_data(value, types=()):
        # Argo's IntOrString/int64 JSON values can be numeric even where the
        # generated SDK declares strings. Match the old client's conversion.
        if types == (str,) and type(value) in (int, float):
            return str(value)
        if isinstance(value, dict):
            model = next((kind for kind in types if isinstance(kind, type) and issubclass(kind, ModelNormal)), None)
            mapping = next((kind for kind in types if isinstance(kind, dict)), {})
            fields = {wire: model.openapi_types[name] for name, wire in model.attribute_map.items()} if model else {}
            item_types = next(iter(mapping.values()), ())
            return {
                key: ApiClient._response_data(item, fields.get(key, item_types))
                for key, item in value.items()
                if item is not None or not fields.get(key, item_types) or type(None) in fields.get(key, item_types)
            }
        if isinstance(value, list):
            item_types = next((kind for kind in types if isinstance(kind, list)), ())
            return [ApiClient._response_data(item, tuple(item_types)) for item in value]
        return value

    @staticmethod
    def _optional_defaults(value):
        if isinstance(value, ModelNormal):
            # The old SDK exposed omitted optional properties as None.
            for name in value.openapi_types:
                value._data_store.setdefault(name, None)
            for item in value._data_store.values():
                ApiClient._optional_defaults(item)
        elif isinstance(value, dict):
            for item in value.values():
                ApiClient._optional_defaults(item)
        elif isinstance(value, list):
            for item in value:
                ApiClient._optional_defaults(item)
        return value

    def deserialize(self, response, response_type, _check_type):
        missing_specs = []
        if response_type in ((V1alpha1Workflow,), (V1alpha1WorkflowList,)):
            data = self._response_data(json.loads(response.data), response_type)
            if response_type == (V1alpha1WorkflowList,):
                data.setdefault("items", [])
                data.setdefault("metadata", {})
                workflows = data["items"]
            else:
                workflows = [data]
            # Argo field projections can omit spec; the newer SDK requires it.
            for workflow in workflows:
                missing_specs.append("spec" not in workflow)
                workflow.setdefault("spec", {})
            response.data = json.dumps(data)
        result = self._optional_defaults(super().deserialize(response, response_type, _check_type))
        if missing_specs:
            workflows = result.items if response_type == (V1alpha1WorkflowList,) else [result]
            for workflow, missing in zip(workflows, missing_specs):
                if missing:
                    workflow._data_store["spec"] = None
        return result


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
    def __init__(self, workflows: V1alpha1WorkflowList):
        self.items = tuple(Workflow(item) for item in workflows.items) if workflows.items is not None else []
        self.continue_token = workflows.metadata._continue if workflows.metadata else None
        self.raw = workflows

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
        options = dict(
            list_options_limit=str(limit) if limit is not None else None,
            list_options_continue=continue_token,
            list_options_label_selector=f"workflows.argoproj.io/phase={status}" if status else None,
            list_options_field_selector=field_selector, fields=fields, **kwargs)
        api_response = service.list_workflows(
            namespace, _request_timeout=timeout_seconds,
            **{key: value for key, value in options.items() if value is not None})

    except ValueError:
        # Exception is raised when no results are found
        return SearchResult(V1alpha1WorkflowList(items=[], metadata={}))
    except exceptions.ApiException as e:
        raise WorkflowException(400, e.body)
    else:
        return SearchResult(api_response)


def submit_workflow(spec) -> Workflow:
    log.debug(f"Submitting workflow %s", spec)

    service = WorkflowServiceApi(api_client=get_api_client())

    req = V1alpha1WorkflowCreateRequest(workflow=spec, instance_id=namespace, namespace=namespace, _check_type=False)

    # pprint(service.list_workflows('ch', V1alpha1WorkflowList()))
    wf = service.create_workflow(namespace, req)
    return Workflow(wf)


def delete_workflow(workflow_name):
    service = WorkflowServiceApi(api_client=get_api_client())
    try:
        service.delete_workflow(namespace, workflow_name, delete_options_grace_period_seconds="0")
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
        raise WorkflowException("Workflow failed: " + workflow.get_status_message())

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
