"""
Access workflows using Argo REST API
Reference: https://argoproj.github.io/docs/argo/docs/rest-api.html
https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md
"""
import kubernetes

import yaml
import os
from pathlib import Path

from cloudharness import log

group = 'argoproj.io'
version = 'v1alpha1'

plural = 'workflows'

# determine the namespace of the current app and run the workflow in that namespace
from cloudharness.utils.config import CloudharnessConfig as conf
ch_conf = conf.get_configuration()
namespace = ch_conf and ch_conf.get('namespace','argo-workflows')

CUSTOM_OBJECT_URL = f"/apis/{group}/{version}/{plural}"


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
    NodePending = "Pending"
    NodeRunning = "Running"
    NodeSucceeded = "Succeeded"
    NodeSkipped = "Skipped"
    NodeFailed = "Failed"
    NodeError = "Error"

    @classmethod
    def phases(cls):
        return tuple(value for key, value in cls.__dict__.items() if 'Node' in key)


class Workflow:
    def __init__(self, raw_dict):
        self.name = raw_dict['metadata']['name']
        self.status = raw_dict['status']['phase'] if 'status' in raw_dict else None
        self.create_time = raw_dict['metadata']['creationTimestamp']
        self.raw = raw_dict

    def is_finished(self):
        return self.status in (Phase.NodeError, Phase.NodeSucceeded, Phase.NodeSkipped, Phase.NodeFailed)

    def __str__(self):
        return yaml.dump(self.raw)

    def succeeded(self):
        return self.status == Phase.NodeSucceeded

    def failed(self):
        return self.status == Phase.NodeFailed

    def get_status_message(self):
        return self.raw['status']['message']

class SearchResult:
    def __init__(self, raw_dict):
        self.items = tuple(Workflow(item) for item in raw_dict['items'])
        self.continue_token = raw_dict['metadata']['continue']
        self.raw = raw_dict

    def __str__(self):
        return self.raw

    def __repr__(self):
        return str(self.raw)


# --- Api functions ---    `

def get_api_client():
    configuration = get_configuration()

    # configuration.api_key['authorization'] = 'YOUR_API_KEY' # TODO verify if we need an api key
    api_instance = kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient(configuration))
    return api_instance


def get_configuration():
    try:
        configuration = kubernetes.config.load_incluster_config()

    except:
        log.warning('Kubernetes cluster configuration not found. Trying local configuration')

        try:
            configuration = kubernetes.config.load_kube_config(
                config_file=os.path.join(str(Path.home()), '.kube', 'config'))
        except:
            log.warning('Kubernetes local configuration not found. Using localhost proxy')
            configuration = kubernetes.client.configuration.Configuration()
            host = 'http://localhost:8001'
            configuration.host = host
    return configuration


api_instance = get_api_client()

def check_namespace():
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(get_configuration()))
    try:
        api_response = api_instance.read_namespace(namespace, exact=True)
    except kubernetes.client.rest.ApiException as e:

        raise Exception(f"Namespace for argo workflows does not exist: {namespace}") from e

def create_namespace():
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(get_configuration()))
    body = kubernetes.client.V1Namespace(metadata=kubernetes.client.V1ObjectMeta(name=namespace))  # V1Namespace |


    try:
        api_response = api_instance.create_namespace(body)
    except Exception  as e:
        raise Exception(f"Error creating namespace: {namespace}") from e
try:
    check_namespace()
except Exception as e:
    log.error('Namespace for argo workflows not found', exc_info=e)
    log.info("Creating namespace %s", namespace)
    try:
        create_namespace()
    except Exception as e:
        log.error('Cannot connect with argo', exc_info=e)


def get_workflows(status=None, limit=10, continue_token=None, timeout_seconds=3) -> SearchResult:
    """https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#list_namespaced_custom_object"""
    # Notice: field selector doesn't work though advertised, except fot metadata.name and metadata.namespace https://github.com/kubernetes/kubernetes/issues/51046
    # The filtering by phase can be obtained through labels: https://github.com/argoproj/argo/issues/496

    params = dict(pretty=False, timeout_seconds=timeout_seconds)
    if status is not None:
        if (status not in Phase.phases()):
            raise BadParam(status, 'Status must be one of {}'.format(Phase.phases()))
        params['label_selector'] = f'workflows.argoproj.io/phase={status}'
    api_response = api_instance.list_namespaced_custom_object(group, version, namespace, plural, **params)

    # TODO implement limit and continue, see https://github.com/kubernetes-client/python/issues/965
    # api_response = api_instance.list_cluster_custom_object(group, version, plural, pretty=False, timeout_seconds=timeout_seconds, watch=watch, limit=limit, continue_token=continue_token)
    return SearchResult(api_response)


def submit_workflow(spec) -> Workflow:
    """https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#create_namespaced_custom_object"""
    log.debug(f"Submitting workflow\n{spec}")
    workflow = Workflow(
        api_instance.create_namespaced_custom_object(group, version, namespace, plural, spec, pretty=False))
    log.info(f"Submitted argo workflow {workflow.name}")
    if workflow.failed():
        raise WorkflowException("Workflow failed: " + workflow.get_status_message())
    return workflow


def delete_workflow(workflow_name):
    """https://github.com/kubernetes-client/python/blob/release-11.0/kubernetes/docs/CustomObjectsApi.md#delete_namespaced_custom_object"""
    try:
        api_instance.delete_namespaced_custom_object(group, version, namespace, plural, workflow_name,
                                                     kubernetes.client.V1DeleteOptions(), grace_period_seconds=0)
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise WorkflowNotFound()
        raise WorkflowException(e.status) from e


def get_workflow(workflow_name) -> Workflow:
    try:
        workflow = Workflow(api_instance.get_namespaced_custom_object(group, version, namespace, plural, workflow_name))
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise WorkflowNotFound()
        raise WorkflowException(e.status) from e
    if workflow.failed():
        raise WorkflowException("Workflow failed: " + workflow.get_status_message())
    return workflow

def get_workflow_logs(workflow_name) -> str:
    core_api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(get_configuration()))
    
    try:
        wf = api_instance.get_namespaced_custom_object(group, version, namespace, plural, workflow_name)
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise WorkflowNotFound()
        raise WorkflowException(e.status) from e
    
    pod_names = [node['id'] for node in wf['status']['nodes'].values() if not 'children' in node]
    
    if len(pod_names) == 0:
        return ''

    try:
        return core_api_instance.read_namespaced_pod_log(name=pod_names[0], namespace=namespace, container="main")
    except kubernetes.client.rest.ApiException as e:
        if e.status == 400:
            return "This step has not emitted logs yet..."
        raise WorkflowException(e.status) from e


if __name__ == '__main__':
    from pprint import pprint

    pprint(CUSTOM_OBJECT_URL)
    pprint(get_workflows('Succeeded').raw)
    # pprint(get_workflow('hello-world-sfzd4'))
