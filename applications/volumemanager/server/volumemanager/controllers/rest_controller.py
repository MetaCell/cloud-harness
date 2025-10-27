import connexion
import six
import flask
import re

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

    # Extract access mode safely
    access_mode = pvc.status.access_modes[0] if pvc.status.access_modes else ''
    
    pvc_response = PersistentVolumeClaim(
        name=pvc.metadata.name,
        namespace=pvc.metadata.namespace,
        accessmode=access_mode,
        size=pvc.status.capacity.get('storage', '')
    )
    return pvc_response


def pvc_post():  # noqa: E501
    """Used to create a Persistent Volume Claim in Kubernetes

     # noqa: E501

    :param persistent_volume_claim_create: The Persistent Volume Claim to create.
    :type persistent_volume_claim_create: dict | bytes

    :rtype: PersistentVolumeClaim
    """
    if connexion.request.is_json:
        persistent_volume_claim_create = PersistentVolumeClaimCreate.from_dict(connexion.request.get_json())  # noqa: E501
        
        # Validate required fields
        if not persistent_volume_claim_create.name or not persistent_volume_claim_create.size:
            return {'description': 'Name and size are required and cannot be empty.'}, 400
        
        # Validate name format (Kubernetes DNS-1123 subdomain)
        name_pattern = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
        if not name_pattern.match(persistent_volume_claim_create.name) or len(persistent_volume_claim_create.name) > 253:
            return {'description': 'Name must be a valid DNS-1123 subdomain (lowercase alphanumeric characters, "-", and must start and end with an alphanumeric character, max 253 characters).'}, 400
        
        # Validate size format
        size_pattern = re.compile(r'^[1-9][0-9]*(Ei|Pi|Ti|Gi|Mi|Ki|E|P|T|G|M|K)?$')
        if not size_pattern.match(persistent_volume_claim_create.size):
            return {'description': 'Size must be a valid Kubernetes resource quantity (e.g., 2Gi, 500Mi).'}, 400
        
        try:
            create_persistent_volume_claim(
                name=persistent_volume_claim_create.name,
                size=persistent_volume_claim_create.size,
                logger=flask.current_app.logger)
        except Exception as e:
            flask.current_app.logger.error(f"Error creating PVC: {e}")
            return {'description': f'Failed to create Persistent Volume Claim: {str(e)}'}, 500
    return 'Saved!', 201
