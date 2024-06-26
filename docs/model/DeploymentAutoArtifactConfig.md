# cloudharness_model.model.deployment_auto_artifact_config.DeploymentAutoArtifactConfig

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Composed Schemas (allOf/anyOf/oneOf/not)
#### allOf
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
[all_of_0](#all_of_0) | dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 
[AutoArtifactSpec](AutoArtifactSpec.md) | [**AutoArtifactSpec**](AutoArtifactSpec.md) | [**AutoArtifactSpec**](AutoArtifactSpec.md) |  | 

# all_of_0

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**port** | str,  | str,  | Deployment port | [optional] 
**replicas** | decimal.Decimal, int,  | decimal.Decimal,  | Number of replicas | [optional] 
**image** | str,  | str,  | Image name to use in the deployment. Leave it blank to set from the application&#x27;s Docker file | [optional] 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | [optional] 
**volume** | [**DeploymentVolumeSpec**](DeploymentVolumeSpec.md) | [**DeploymentVolumeSpec**](DeploymentVolumeSpec.md) |  | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

