# SampleResource



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**a** | **float** |  | 
**b** | **float** |  | [optional] 
**id** | **float** |  | [optional] 

## Example

```python
from cloudharness_cli.samples.models.sample_resource import SampleResource

# TODO update the JSON string below
json = "{}"
# create an instance of SampleResource from a JSON string
sample_resource_instance = SampleResource.from_json(json)
# print the JSON string representation of the object
print(SampleResource.to_json())

# convert the object into a dict
sample_resource_dict = sample_resource_instance.to_dict()
# create an instance of SampleResource from a dict
sample_resource_from_dict = SampleResource.from_dict(sample_resource_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


