# DeploymentVolumeSpec

Defines a volume attached to the deployment. Automatically created the volume claim and mounts.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | [optional] 
**name** | **str** |  | [optional] 
**mountpath** | **str** | The mount path for the volume | 
**size** | **object** | The volume size.   E.g. 5Gi | [optional] 
**usenfs** | **bool** | Deprecated: use &#x60;writeMany&#x60; with the nfs storage class instead.  Set to &#x60;true&#x60; to use the nfs on the created volume and mount as ReadWriteMany. | [optional] 
**write_many** | **bool** | Set to &#x60;true&#x60; to create and mount the volume as ReadWriteMany.  ReadWriteMany volumes attach to several nodes at once, hence pods using them are not pinned to the volume&#39;s node. Requires a storage class supporting ReadWriteMany: set &#x60;storageClass&#x60;, unless the cluster default one supports it. | [optional] 
**storage_class** | **str** | The storage class used to create the volume claim, &#x60;standard&#x60; by default.  Set it to null to omit the storage class from the claim, so that the cluster default storage class is used. | [optional] 

## Example

```python
from cloudharness_model.models.deployment_volume_spec import DeploymentVolumeSpec

# TODO update the JSON string below
json = "{}"
# create an instance of DeploymentVolumeSpec from a JSON string
deployment_volume_spec_instance = DeploymentVolumeSpec.from_json(json)
# print the JSON string representation of the object
print(DeploymentVolumeSpec.to_json())

# convert the object into a dict
deployment_volume_spec_dict = deployment_volume_spec_instance.to_dict()
# create an instance of DeploymentVolumeSpec from a dict
deployment_volume_spec_from_dict = DeploymentVolumeSpec.from_dict(deployment_volume_spec_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


