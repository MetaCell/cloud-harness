# DatabaseDeploymentConfigAllOf


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** | Define the database type.  One of (mongo, postgres, neo4j) | [optional] 
**size** | **str** | Specify database disk size | [optional] 
**user** | **str** | database username | [optional] 
**_pass** | **str** | Database password | [optional] 
**mongo** | [**FreeObject**](FreeObject.md) |  | [optional] 
**postgres** | [**FreeObject**](FreeObject.md) |  | [optional] 
**neo4j** | **bool, date, datetime, dict, float, int, list, str, none_type** | Neo4j database specific configuration | [optional] 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


