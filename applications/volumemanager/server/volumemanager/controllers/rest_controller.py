import connexion
import six
import flask

from cloudharness.service.pvc import create_persistent_volume_claim, get_persistent_volume_claim

from volumemanager.models.persistent_volume_claim import PersistentVolumeClaim  # noqa: E501
from volumemanager.models.persistent_volume_claim_create import PersistentVolumeClaimCreate  # noqa: E501
from volumemanager import util


def pvc_name_get(name):  # noqa: E501
    """Used to retrieve a Persistent Volume Claim from the Kubernetes repository.

     # noqa: E501

    :param name: The name of the Persistent Volume Claim to be retrieved
    :type name: str

    :rtype: PersistentVolumeClaim
    """
    pvc = get_persistent_volume_claim(name)
    if not pvc:
        return f"Persistent Volume Claim with name {name} not found.", 404

    pvc = PersistentVolumeClaim(
        name=pvc.metadata.name,
        namespace=pvc.metadata.namespace,
        accessmode=pvc.status.access_modes[0],
        size=pvc.status.capacity.get('storage', '')
    )
    return pvc


def pvc_post():  # noqa: E501
    """Used to create a Persistent Volume Claim in Kubernetes

     # noqa: E501

    :param persistent_volume_claim_create: The Persistent Volume Claim to create.
    :type persistent_volume_claim_create: dict | bytes

    :rtype: PersistentVolumeClaim
    """
    if connexion.request.is_json:
        persistent_volume_claim_create = PersistentVolumeClaimCreate.from_dict(connexion.request.get_json())  # noqa: E501
        
        # Validate required fields (backup if Connexion doesn't catch it)
        if not persistent_volume_claim_create.name or not persistent_volume_claim_create.size:
            return {'description': 'Name and size are required and cannot be empty.'}, 400
        
        try:
            create_persistent_volume_claim(
                name=persistent_volume_claim_create.name,
                size=persistent_volume_claim_create.size,
                logger=flask.current_app.logger)
        except Exception as e:
            flask.current_app.logger.error(f"Error creating PVC: {e}")
            return {'description': f'Failed to create Persistent Volume Claim: {str(e)}'}, 500
    return 'Saved!', 201
