# DatabaseDeploymentConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | 
**name** | **str** |  | [optional] 
**type** | **str** | Define the database type.  One of (mongo, postgres, neo4j, sqlite3) | [optional] 
**size** | **str** | Specify database disk size | [optional] 
**user** | **str** | database username | [optional] 
**var_pass** | **str** | Database password | [optional] 
**image_ref** | **str** | Used for referencing images from the build | [optional] 
**mongo** | **Dict[str, object]** |  | [optional] 
**postgres** | **Dict[str, object]** |  | [optional] 
**neo4j** | **object** | Neo4j database specific configuration | [optional] 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.database_deployment_config import DatabaseDeploymentConfig

# TODO update the JSON string below
json = "{}"
# create an instance of DatabaseDeploymentConfig from a JSON string
database_deployment_config_instance = DatabaseDeploymentConfig.from_json(json)
# print the JSON string representation of the object
print DatabaseDeploymentConfig.to_json()

# convert the object into a dict
database_deployment_config_dict = database_deployment_config_instance.to_dict()
# create an instance of DatabaseDeploymentConfig from a dict
database_deployment_config_form_dict = database_deployment_config.from_dict(database_deployment_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


