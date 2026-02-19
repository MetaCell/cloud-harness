# FileResourcesConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**src** | **str** |  | 
**dst** | **str** |  | 

## Example

```python
from cloudharness_model.models.file_resources_config import FileResourcesConfig

# TODO update the JSON string below
json = "{}"
# create an instance of FileResourcesConfig from a JSON string
file_resources_config_instance = FileResourcesConfig.from_json(json)
# print the JSON string representation of the object
print(FileResourcesConfig.to_json())

# convert the object into a dict
file_resources_config_dict = file_resources_config_instance.to_dict()
# create an instance of FileResourcesConfig from a dict
file_resources_config_from_dict = FileResourcesConfig.from_dict(file_resources_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


