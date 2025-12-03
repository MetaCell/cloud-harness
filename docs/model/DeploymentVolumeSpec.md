# DeploymentVolumeSpec

Defines a volume attached to the deployment. Automatically created the volume claim and mounts.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | 
**name** | **str** |  | [optional] 
**mountpath** | **str** | The mount path for the volume | 
**size** | **object** | The volume size.   E.g. 5Gi | [optional] 
**usenfs** | **bool** | Set to &#x60;true&#x60; to use the nfs on the created volume and mount as ReadWriteMany. | [optional] 

## Example

```python
from cloudharness_model.models.deployment_volume_spec import DeploymentVolumeSpec

# TODO update the JSON string below
json = "{}"
# create an instance of DeploymentVolumeSpec from a JSON string
deployment_volume_spec_instance = DeploymentVolumeSpec.from_json(json)
# print the JSON string representation of the object
print DeploymentVolumeSpec.to_json()

# convert the object into a dict
deployment_volume_spec_dict = deployment_volume_spec_instance.to_dict()
# create an instance of DeploymentVolumeSpec from a dict
deployment_volume_spec_form_dict = deployment_volume_spec.from_dict(deployment_volume_spec_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


