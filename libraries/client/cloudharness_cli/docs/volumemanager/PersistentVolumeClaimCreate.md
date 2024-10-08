# PersistentVolumeClaimCreate


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Unique name for the Persisten Volume Claim to create. | [optional] 
**size** | **str** | The size of the Persistent Volume Claim to create. | [optional] 

## Example

```python
from cloudharness_cli.volumemanager.models.persistent_volume_claim_create import PersistentVolumeClaimCreate

# TODO update the JSON string below
json = "{}"
# create an instance of PersistentVolumeClaimCreate from a JSON string
persistent_volume_claim_create_instance = PersistentVolumeClaimCreate.from_json(json)
# print the JSON string representation of the object
print(PersistentVolumeClaimCreate.to_json())

# convert the object into a dict
persistent_volume_claim_create_dict = persistent_volume_claim_create_instance.to_dict()
# create an instance of PersistentVolumeClaimCreate from a dict
persistent_volume_claim_create_from_dict = PersistentVolumeClaimCreate.from_dict(persistent_volume_claim_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


