import connexion
import six

from samples.models.sample_resource import SampleResource  # noqa: E501
from samples import util
from samples.service import resource_service


def create_sample_resource(sample_resource=None):  # noqa: E501
    """Create a SampleResource

    Creates a new instance of a &#x60;SampleResource&#x60;. # noqa: E501

    :param sample_resource: A new &#x60;SampleResource&#x60; to be created.
    :type sample_resource: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        try:
            sample_resource = SampleResource.from_dict(connexion.request.get_json())  # noqa: E501
        except:
            return "Payload is not of type SampleResource", 400
    return resource_service.create_sample_resource(sample_resource), 201


def delete_sample_resource(sampleresource_id):  # noqa: E501
    """Delete a SampleResource

    Deletes an existing &#x60;SampleResource&#x60;. # noqa: E501

    :param sampleresource_id: A unique identifier for a &#x60;SampleResource&#x60;.
    :type sampleresource_id: str

    :rtype: None
    """
    try:
        resource_service.delete_sample_resource(int(sampleresource_id))
    except resource_service.ResourceNotFound:
        return "Resource not found", 404
    except ValueError:
        return "sampleresource_id must be integer", 400
    return 'OK', 204


def get_sample_resource(sampleresource_id):  # noqa: E501
    """Get a SampleResource

    Gets the details of a single instance of a &#x60;SampleResource&#x60;. # noqa: E501

    :param sampleresource_id: A unique identifier for a &#x60;SampleResource&#x60;.
    :type sampleresource_id: str

    :rtype: SampleResource
    """
    try:
        resource = resource_service.get_sample_resource(int(sampleresource_id))
        return resource, 200
    except resource_service.ResourceNotFound:
        return "Resource not found", 404
    except ValueError:
        return "sampleresource_id must be integer", 400


def get_sample_resources():  # noqa: E501
    """List All SampleResources

    Gets a list of all &#x60;SampleResource&#x60; entities. # noqa: E501


    :rtype: List[SampleResource]
    """
    return resource_service.get_sample_resources()


def update_sample_resource(sampleresource_id, sample_resource=None):  # noqa: E501
    """Update a SampleResource

    Updates an existing &#x60;SampleResource&#x60;. # noqa: E501

    :param sampleresource_id: A unique identifier for a &#x60;SampleResource&#x60;.
    :type sampleresource_id: str
    :param sample_resource: Updated &#x60;SampleResource&#x60; information.
    :type sample_resource: dict | bytes

    :rtype: None
    """
    try:
        sample_resource = SampleResource.from_dict(connexion.request.get_json())  # noqa: E501
    except:
        return "Payload is not of type SampleResource", 400
    try:
        resource = resource_service.update_sample_resource(
            int(sampleresource_id), sample_resource)
        return resource, 202
    except resource_service.ResourceNotFound:
        return "Resource not found", 404
    except ValueError:
        return "sampleresource_id must be integer", 400
