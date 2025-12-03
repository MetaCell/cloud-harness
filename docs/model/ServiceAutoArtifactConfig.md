# ServiceAutoArtifactConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | 
**name** | **str** |  | [optional] 
**port** | **int** | Service port | [optional] 

## Example

```python
from cloudharness_model.models.service_auto_artifact_config import ServiceAutoArtifactConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ServiceAutoArtifactConfig from a JSON string
service_auto_artifact_config_instance = ServiceAutoArtifactConfig.from_json(json)
# print the JSON string representation of the object
print ServiceAutoArtifactConfig.to_json()

# convert the object into a dict
service_auto_artifact_config_dict = service_auto_artifact_config_instance.to_dict()
# create an instance of ServiceAutoArtifactConfig from a dict
service_auto_artifact_config_form_dict = service_auto_artifact_config.from_dict(service_auto_artifact_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


