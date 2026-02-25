# RegistrySecretConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The name of the secret to create for docker registry credentials | 
**value** | **str** | The value of the secret to create for docker registry credentials. The value should be the base64 encoded content of a .dockerconfigjson file. | [optional] 

## Example

```python
from cloudharness_model.models.registry_secret_config import RegistrySecretConfig

# TODO update the JSON string below
json = "{}"
# create an instance of RegistrySecretConfig from a JSON string
registry_secret_config_instance = RegistrySecretConfig.from_json(json)
# print the JSON string representation of the object
print(RegistrySecretConfig.to_json())

# convert the object into a dict
registry_secret_config_dict = registry_secret_config_instance.to_dict()
# create an instance of RegistrySecretConfig from a dict
registry_secret_config_from_dict = RegistrySecretConfig.from_dict(registry_secret_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


