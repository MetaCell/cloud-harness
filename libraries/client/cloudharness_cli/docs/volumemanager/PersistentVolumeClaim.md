# PersistentVolumeClaim


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Unique name for the Persisten Volume Claim | [optional] 
**namespace** | **str** | The namespace where the Persistent Volume Claim resides in | [optional] 
**accessmode** | **str** | The accessmode of the Persistent Volume Claim | [optional] 
**size** | **str** | The size of the Persistent Volume Claim. | [optional] 

## Example

```python
from cloudharness_cli.volumemanager.models.persistent_volume_claim import PersistentVolumeClaim

# TODO update the JSON string below
json = "{}"
# create an instance of PersistentVolumeClaim from a JSON string
persistent_volume_claim_instance = PersistentVolumeClaim.from_json(json)
# print the JSON string representation of the object
print(PersistentVolumeClaim.to_json())

# convert the object into a dict
persistent_volume_claim_dict = persistent_volume_claim_instance.to_dict()
# create an instance of PersistentVolumeClaim from a dict
persistent_volume_claim_from_dict = PersistentVolumeClaim.from_dict(persistent_volume_claim_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


