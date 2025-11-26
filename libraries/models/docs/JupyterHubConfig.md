# JupyterHubConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**args** | **List[str]** | arguments passed to the container | [optional] 
**extra_config** | **Dict[str, object]** |  | [optional] 
**spawner_extra_config** | **Dict[str, object]** |  | [optional] 
**application_hook** | **object** | change the hook function (advanced)  Specify the Python name of the function (full module path, the module must be  installed in the Docker image) | [optional] 

## Example

```python
from cloudharness_model.models.jupyter_hub_config import JupyterHubConfig

# TODO update the JSON string below
json = "{}"
# create an instance of JupyterHubConfig from a JSON string
jupyter_hub_config_instance = JupyterHubConfig.from_json(json)
# print the JSON string representation of the object
print(JupyterHubConfig.to_json())

# convert the object into a dict
jupyter_hub_config_dict = jupyter_hub_config_instance.to_dict()
# create an instance of JupyterHubConfig from a dict
jupyter_hub_config_from_dict = JupyterHubConfig.from_dict(jupyter_hub_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


