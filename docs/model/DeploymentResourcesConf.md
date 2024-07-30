# DeploymentResourcesConf



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**requests** | [**CpuMemoryConfig**](CpuMemoryConfig.md) |  | [optional] 
**limits** | [**CpuMemoryConfig**](CpuMemoryConfig.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.deployment_resources_conf import DeploymentResourcesConf

# TODO update the JSON string below
json = "{}"
# create an instance of DeploymentResourcesConf from a JSON string
deployment_resources_conf_instance = DeploymentResourcesConf.from_json(json)
# print the JSON string representation of the object
print DeploymentResourcesConf.to_json()

# convert the object into a dict
deployment_resources_conf_dict = deployment_resources_conf_instance.to_dict()
# create an instance of DeploymentResourcesConf from a dict
deployment_resources_conf_form_dict = deployment_resources_conf.from_dict(deployment_resources_conf_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


