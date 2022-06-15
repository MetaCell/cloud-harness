import connexion
import six

from samples.models.sample_resource import SampleResource  # noqa: E501
from samples import util


def create_sample_resource(sample_resource=None):  # noqa: E501
    """Create a SampleResource

    Creates a new instance of a &#x60;SampleResource&#x60;. # noqa: E501

    :param sample_resource: A new &#x60;SampleResource&#x60; to be created.
    :type sample_resource: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        sample_resource = SampleResource.from_dict(connexion.request.get_json())  # noqa: E501
    return sample_resource


def delete_sample_resource(sampleresource_id):  # noqa: E501
    """Delete a SampleResource

    Deletes an existing &#x60;SampleResource&#x60;. # noqa: E501

    :param sampleresource_id: A unique identifier for a &#x60;SampleResource&#x60;.
    :type sampleresource_id: str

    :rtype: None
    """
    return 'OK'


def get_sample_resource(sampleresource_id):  # noqa: E501
    """Get a SampleResource

    Gets the details of a single instance of a &#x60;SampleResource&#x60;. # noqa: E501

    :param sampleresource_id: A unique identifier for a &#x60;SampleResource&#x60;.
    :type sampleresource_id: str

    :rtype: SampleResource
    """
    return SampleResource(a=1, b=2).to_dict()


def get_sample_resources():  # noqa: E501
    """List All SampleResources

    Gets a list of all &#x60;SampleResource&#x60; entities. # noqa: E501


    :rtype: List[SampleResource]
    """
    return [SampleResource(a=1, b=2), SampleResource(a=3, b=4)]


def update_sample_resource(sampleresource_id, sample_resource=None):  # noqa: E501
    """Update a SampleResource

    Updates an existing &#x60;SampleResource&#x60;. # noqa: E501

    :param sampleresource_id: A unique identifier for a &#x60;SampleResource&#x60;.
    :type sampleresource_id: str
    :param sample_resource: Updated &#x60;SampleResource&#x60; information.
    :type sample_resource: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        sample_resource = SampleResource.from_dict(connexion.request.get_json())  # noqa: E501
    return sample_resource
