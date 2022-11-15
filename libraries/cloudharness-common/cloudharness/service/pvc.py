import os
import kubernetes
import yaml

from cloudharness.utils.config import CloudharnessConfig as conf
from cloudharness.utils import dict_merge


def _get_client():
    try:
        configuration = kubernetes.config.load_incluster_config()
    except:
        configuration = kubernetes.config.load_kube_config()
    return kubernetes.client.ApiClient(configuration)


def _get_corev1_api():
    return kubernetes.client.CoreV1Api(_get_client())


def _get_nfs_storage_class() -> str:
    """
    NFS storage class

    :return:    Returns the NFS storage class name that belongs
                to this namespace (deployment)
    """
    nfsserver_conf = conf.get_application_by_filter(storageClass__name=True)[0]
    return f"{conf.get_configuration()['namespace']}-{nfsserver_conf['storageClass']['name']}"


def _get_default_storage_class() -> str:
    """
    Default storage class

    :return:    Returns the default storage class name, if exists.
                If not, it returns the first storage class.
                If there are not storage classes, returns None
    """

    storagev1 = kubernetes.client.StorageV1Api(_get_client())
    storage_classes = storagev1.list_storage_class()
    selected_sc = None
    default_sc_annotations = {
        "storageclass.kubernetes.io/is-default-class": "true",
        # Older clusters still use the beta annotation.
        "storageclass.beta.kubernetes.io/is-default-class": "true",
    }

    # default to the first if there is no default
    selected_sc = storage_classes.items[0].metadata.name

    for sc in storage_classes.items:
        if not selected_sc:
            # Select the first storage class in case there is no a default-class
            selected_sc = sc.metadata.name
        annotations = sc.metadata.annotations
        if any(
            k in annotations and annotations[k] == v
            for k, v in default_sc_annotations.items()
        ):
            # Default storage
            selected_sc = sc.metadata.name
            break
    return selected_sc

def create_persistent_volume_claim(name, size, logger, storage_class=None, useNFS=False, template=None, access_mode=None, **kwargs):
    """
    Create a Persistent Volume Claim in the Kubernetes cluster.
    If a PVC with the name given already exists then the function
    will just return to the caller function.

    Args:
        name (string): the name of the PVC
        size (string): the size of the PVC, e.g. 2Gi for a 2Gb PVC
        logger (logger): the logger where the information message is sent to
        storage_class (string, optional): the name of the K8s storage class to use
        useNFS (boolean, default False): if set to True CH will search
          for the storage class that is linked to the local CH NFS Server
        template (text, optional): the template to use to create the PVC
        **kwargs - the dictionary is used to override the default template
    Returns:
        -
    """
    if persistent_volume_claim_exists(name):
        return

    if not size:
        raise Exception(f"Size must be set. Got {size!r}.")
    
    if not storage_class:
        if not useNFS:
            storage_class = _get_default_storage_class()
        else:
            # determine the NFS storage class
            storage_class = _get_nfs_storage_class()

    if not access_mode and useNFS:
        access_mode = "ReadWriteMany"

    if not template:
        path = os.path.join(os.path.dirname(__file__), 'templates', 'pvc.yaml')
        template = open(path, 'rt').read()
    text = template.format(
            name=name,
            size=size,
            storageClass=storage_class)
    data = dict_merge(yaml.safe_load(text), kwargs)

    if access_mode:
        data["spec"]["accessModes"] = [access_mode]

    obj = _get_corev1_api().create_namespaced_persistent_volume_claim(
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
    foundPVCs = _get_corev1_api().list_namespaced_persistent_volume_claim(
        namespace=conf.get_configuration()['namespace'],
        field_selector=f'metadata.name={name}')
    if len(foundPVCs.items) > 0:
        return foundPVCs.items[0]
    return None


def delete_persistent_volume_claim(name):
    _get_corev1_api().delete_namespaced_persistent_volume_claim(
        name=name,
        namespace=conf.get_configuration()['namespace'])
