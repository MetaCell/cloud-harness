"""
Sample service layer for resource management
"""

from typing import List
from samples.models import SampleResource

counter = 0
resources = {}

class ResourceNotFound(Exception):
    pass


def create_sample_resource(sample_resource: SampleResource):  # noqa: E501
    global counter

    counter += 1
    sample_resource.id = counter
    resources[sample_resource.id] = sample_resource
    return sample_resource


def delete_sample_resource(sampleresource_id: int):  # noqa: E501
    if sampleresource_id not in resources:
        raise ResourceNotFound()
    del resources[sampleresource_id]


def get_sample_resource(sampleresource_id: int):  # noqa: E501
    if sampleresource_id not in resources:
        raise ResourceNotFound()
    return resources[sampleresource_id]


def get_sample_resources() -> List[SampleResource]:
    return [v for v in resources.values()] 


def update_sample_resource(sampleresource_id: int, sample_resource: SampleResource) -> List[SampleResource]:
    if sampleresource_id not in resources:
        raise ResourceNotFound()
    resources[sampleresource_id] = sample_resource
    return resources[sampleresource_id]
