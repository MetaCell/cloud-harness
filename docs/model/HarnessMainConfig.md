# HarnessMainConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**local** | **bool** | If set to true, local DNS mapping is added to pods. | 
**secured_gatekeepers** | **bool** | Enables/disables Gatekeepers on secured applications. Set to false for testing/development | 
**domain** | **str** | The root domain | 
**namespace** | **str** | The K8s namespace. | 
**mainapp** | **str** | Defines the app to map to the root domain | 
**registry** | [**RegistryConfig**](RegistryConfig.md) |  | [optional] 
**tag** | **str** | Docker tag used to push/pull the built images. | [optional] 
**apps** | [**Dict[str, ApplicationConfig]**](ApplicationConfig.md) |  | 
**env** | [**List[NameValue]**](NameValue.md) | Environmental variables added to all pods | [optional] 
**privenv** | [**NameValue**](NameValue.md) |  | [optional] 
**backup** | [**BackupConfig**](BackupConfig.md) |  | [optional] 
**name** | **str** | Base name | [optional] 
**task_images** | **Dict[str, str]** |  | [optional] 

## Example

```python
from cloudharness_model.models.harness_main_config import HarnessMainConfig

# TODO update the JSON string below
json = "{}"
# create an instance of HarnessMainConfig from a JSON string
harness_main_config_instance = HarnessMainConfig.from_json(json)
# print the JSON string representation of the object
print(HarnessMainConfig.to_json())

# convert the object into a dict
harness_main_config_dict = harness_main_config_instance.to_dict()
# create an instance of HarnessMainConfig from a dict
harness_main_config_from_dict = HarnessMainConfig.from_dict(harness_main_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


