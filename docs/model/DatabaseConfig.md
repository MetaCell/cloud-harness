# DatabaseConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**image** | **str** |  | [optional] 
**name** | **str** |  | [optional] 
**ports** | [**List[PortConfig]**](PortConfig.md) |  | [optional] 
**operator** | **bool** | Use the CloudNative-PG operator instead of a plain Deployment (postgres only) | [optional] 
**instances** | **int** | Number of PostgreSQL instances managed by the CNPG operator (only used when operator is true) | [optional] 
**api_server_cidr** | **List[str]** | CIDR(s) allowed for CNPG pods to reach the Kubernetes API server (port 443). Override with your cluster API-server or service CIDR. | [optional] 
**initialdb** | **str** | Initial database name (postgres only) | [optional] 
**args** | **List[str]** | Additional command-line arguments passed to the database server process (postgres only) | [optional] 

## Example

```python
from cloudharness_model.models.database_config import DatabaseConfig

# TODO update the JSON string below
json = "{}"
# create an instance of DatabaseConfig from a JSON string
database_config_instance = DatabaseConfig.from_json(json)
# print the JSON string representation of the object
print(DatabaseConfig.to_json())

# convert the object into a dict
database_config_dict = database_config_instance.to_dict()
# create an instance of DatabaseConfig from a dict
database_config_from_dict = DatabaseConfig.from_dict(database_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


