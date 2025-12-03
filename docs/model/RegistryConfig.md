# RegistryConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**secret** | **str** | Optional secret used for pulling from docker registry. | [optional] 

## Example

```python
from cloudharness_model.models.registry_config import RegistryConfig

# TODO update the JSON string below
json = "{}"
# create an instance of RegistryConfig from a JSON string
registry_config_instance = RegistryConfig.from_json(json)
# print the JSON string representation of the object
print RegistryConfig.to_json()

# convert the object into a dict
registry_config_dict = registry_config_instance.to_dict()
# create an instance of RegistryConfig from a dict
registry_config_form_dict = registry_config.from_dict(registry_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


