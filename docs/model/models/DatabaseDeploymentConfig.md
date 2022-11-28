# cloudharness_model.model.database_deployment_config.DatabaseDeploymentConfig

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
**type** | str,  | str,  | Define the database type.  One of (mongo, postgres, neo4j, sqlite3) | [optional] 
**size** | str,  | str,  | Specify database disk size | [optional] 
**user** | str,  | str,  | database username | [optional] 
**pass** | str,  | str,  | Database password | [optional] 
**image_ref** | str,  | str,  | Used for referencing images from the build | [optional] 
**mongo** | [**FreeObject**](FreeObject.md) | [**FreeObject**](FreeObject.md) |  | [optional] 
**postgres** | [**FreeObject**](FreeObject.md) | [**FreeObject**](FreeObject.md) |  | [optional] 
**neo4j** | dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, bool, None, list, tuple, bytes, io.FileIO, io.BufferedReader,  | frozendict.frozendict, str, decimal.Decimal, BoolClass, NoneClass, tuple, bytes, FileIO | Neo4j database specific configuration | [optional] 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

