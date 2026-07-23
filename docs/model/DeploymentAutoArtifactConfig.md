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
**statefulset** | **bool** | When true, the workload is rendered as a Kubernetes StatefulSet instead of a Deployment. Recommended for deployments with a ReadWriteOnce volume: updates terminate the old pod before creating the new one, so no Recreate strategy or node pinning is needed. The volume, unless nfs-shared or externally managed (auto false), is provisioned per replica through volumeClaimTemplates. A pre-existing PVC named after the volume (left over from a previous Deployment) is migrated automatically: a migration job streams its data into each statefulset volume through the Kubernetes API, so the volumes are never mounted by the same pod (works on multi-zone clusters); delete the legacy PVC once migrated. | [optional] 
**network** | [**NetworkConfig**](NetworkConfig.md) |  | [optional] 
**extra_containers** | [**Dict[str, ExtraContainerConfig]**](ExtraContainerConfig.md) | Extra containers (init containers and sidecars) for the deployment. Each key is a container name mapping to an ExtraContainerConfig. | [optional] 

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


