import os
import kubernetes
import yaml

from cloudharness.utils.config import CloudharnessConfig as conf

def _get_api():
    try:
        configuration = kubernetes.config.load_incluster_config()
    except:
        configuration = kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
    return api_instance

def create_persistent_volume_claim(name, size, logger, **kwargs):
    """
    Create a Persistent Volume Claim in the Kubernetes cluster.
    If a PVC with the name given already exists then the function
    will just return to the caller function.

    Args:
        name (string): the name of the PVC
        size (string): the size of the PVC, e.g. 2Gi for a 2Gb PVC
        logger (logger): the logger where the information message is sent to

    Returns:
        -
    """
    if not size:
        raise Exception(f"Size must be set. Got {size!r}.")

    if not persistent_volume_claim_exists(name):
        path = os.path.join(os.path.dirname(__file__), 'templates', 'pvc.yaml')
        tmpl = open(path, 'rt').read()
        text = tmpl.format(name=name, size=size)
        data = yaml.safe_load(text)

        obj = _get_api().create_namespaced_persistent_volume_claim(
            namespace=conf.get_configuration()['namespace'],
            body=data,
        )
        logger.info(f"PVC child is created: %s", obj)

def persistent_volume_claim_exists(name):
    """
    Check if the PVC with the given name already exists.

    Args:
        name (string): the name of the PVC
      
    Returns:
        boolean: True if the PVC exists, False is the PVC doesn't exist
    """
    if get_persistent_volume_claim(name):
        return True
    return False

def get_persistent_volume_claim(name):
    """
    Get the Persistent Volume Claim with the given name from the Kubernetes
    cluster.

    Args:
        name (string): the name of the PVC

    Returns:
        The PVC data (see https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
    """
    foundPVCs = _get_api().list_namespaced_persistent_volume_claim(
        namespace=conf.get_configuration()['namespace'],
        field_selector=f'metadata.name={name}')
    if len(foundPVCs.items)>0:
        return foundPVCs.items[0]
    return None
