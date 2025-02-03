# CpuMemoryConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cpu** | **str** |  | [optional] 
**memory** | **str** |  | [optional] 

## Example

```python
from cloudharness_model.models.cpu_memory_config import CpuMemoryConfig

# TODO update the JSON string below
json = "{}"
# create an instance of CpuMemoryConfig from a JSON string
cpu_memory_config_instance = CpuMemoryConfig.from_json(json)
# print the JSON string representation of the object
print CpuMemoryConfig.to_json()

# convert the object into a dict
cpu_memory_config_dict = cpu_memory_config_instance.to_dict()
# create an instance of CpuMemoryConfig from a dict
cpu_memory_config_form_dict = cpu_memory_config.from_dict(cpu_memory_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


