# ExtraContainerConfig

Configuration for an extra container (init container or sidecar) in a deployment

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, the extra container is included in the deployment | [optional] 
**init_container** | **bool** | When true, the container runs as a Kubernetes init container (before the main container). When false, the container runs as a sidecar (alongside the main container). | [optional] 
**image** | **str** | Docker image for the extra container. If not specified, defaults to the main application image. | [optional] 
**commands** | **List[str]** | Command to run in the extra container | [optional] 
**share_volume** | **bool** | When true, the extra container shares the same volume mounts as the main container. | [optional] 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.extra_container_config import ExtraContainerConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ExtraContainerConfig from a JSON string
extra_container_config_instance = ExtraContainerConfig.from_json(json)
# print the JSON string representation of the object
print(ExtraContainerConfig.to_json())

# convert the object into a dict
extra_container_config_dict = extra_container_config_instance.to_dict()
# create an instance of ExtraContainerConfig from a dict
extra_container_config_from_dict = ExtraContainerConfig.from_dict(extra_container_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


