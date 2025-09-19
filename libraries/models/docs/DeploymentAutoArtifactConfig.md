# DeploymentAutoArtifactConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | [optional] 
**name** | **str** |  | [optional] 
**port** | **object** | Deployment port | [optional] 
**replicas** | **int** | Number of replicas | [optional] 
**image** | **str** | Image name to use in the deployment. Leave it blank to set from the application&#39;s Docker file | [optional] 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | [optional] 
**volume** | [**DeploymentVolumeSpec**](DeploymentVolumeSpec.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.deployment_auto_artifact_config import DeploymentAutoArtifactConfig

# TODO update the JSON string below
json = "{}"
# create an instance of DeploymentAutoArtifactConfig from a JSON string
deployment_auto_artifact_config_instance = DeploymentAutoArtifactConfig.from_json(json)
# print the JSON string representation of the object
print(DeploymentAutoArtifactConfig.to_json())

# convert the object into a dict
deployment_auto_artifact_config_dict = deployment_auto_artifact_config_instance.to_dict()
# create an instance of DeploymentAutoArtifactConfig from a dict
deployment_auto_artifact_config_from_dict = DeploymentAutoArtifactConfig.from_dict(deployment_auto_artifact_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


