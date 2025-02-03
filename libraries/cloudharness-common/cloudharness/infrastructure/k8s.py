"""
Kubernetes base api.

TODO: stubs for configuration and running queries are working, but not much functionality at the moment
"""
import kubernetes

from cloudharness import log

# TODO handle group

from cloudharness.utils.config import CloudharnessConfig as conf


# determine the namespace of the current app and run the workflow in that namespace

namespace = conf.get_namespace()

version = 'v1alpha1'

# --- Api functions ---    `


def get_api_client():
    configuration = get_configuration()
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(get_configuration()))
    return api_instance


def get_configuration():
    try:
        configuration = kubernetes.config.load_incluster_config()
    except:
        log.warning('Kubernetes cluster configuration not found. Trying local configuration')
        try:
            configuration = kubernetes.config.load_kube_config()
        except:
            log.warning('Kubernetes local configuration not found. Using localhost proxy')
            configuration = kubernetes.client.configuration.Configuration()
    return configuration


api_instance = get_api_client()


def create_namespace():
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(get_configuration()))
    body = kubernetes.client.V1Namespace(metadata=kubernetes.client.V1ObjectMeta(name=namespace))  # V1Namespace |

    try:
        api_response = api_instance.create_namespace(body)
    except Exception as e:
        raise Exception(f"Error creating namespace: {namespace}") from e


def get_objects(group='argoproj.io', plural='workflows', status=None, limit=10, continue_token=None, timeout_seconds=3):
    """https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#list_namespaced_custom_object"""
    # Notice: field selector doesn't work though advertised, except fot metadata.name and metadata.namespace https://github.com/kubernetes/kubernetes/issues/51046
    # The filtering by phase can be obtained through labels: https://github.com/argoproj/argo/issues/496

    params = dict(pretty=False, timeout_seconds=timeout_seconds)

    api_response = api_instance.list_namespaced_custom_object(group, version, namespace, plural, **params)
    return api_response


def get_object(object_name):
    configuration = get_configuration()
    api_instance = kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient(configuration))
    return api_instance.get_namespaced_custom_object(group, version, namespace, plural, object_name)


def get_pod_logs(pod_name, namespace=namespace):
    try:
        return api_instance.read_namespaced_pod_log(name=pod_name, namespace=namespace, container="main")
    except kubernetes.client.rest.ApiException as e:
        if e.status == 400:
            return f"Pod {pod_name} has not emitted logs yet..."
        raise Exception(e.status) from e


def get_pod(pod_name, namespace=namespace):
    try:
        return api_instance.read_namespaced_pod(name=pod_name, namespace=namespace)
    except kubernetes.client.rest.ApiException as e:
        if 404 == e.status:
            raise Exception(f"Pod {pod_name} not found")
        raise Exception(e.status) from e


def get_pods(namespace=namespace):
    try:
        return api_instance.list_namespaced_pod(namespace=namespace)
    except kubernetes.client.rest.ApiException as e:
        raise Exception("Error retrieving pods") from e


def get_deployments(namespace=namespace):
    api_instance = kubernetes.client.AppsV1Api(kubernetes.client.ApiClient(get_configuration()))
    try:
        return api_instance.list_namespaced_deployment(namespace=namespace)
    except kubernetes.client.rest.ApiException as e:
        raise Exception("Error retrieving deployments") from e


if __name__ == '__main__':
    from pprint import pprint

    pprint(get_objects())
