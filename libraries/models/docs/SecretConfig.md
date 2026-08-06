# SecretConfig

Rich definition of an application secret, used in place of a plain value to delegate the secret to a secret manager. Manager specific settings (e.g. `path` for onepassword, `arn` for aws) are added next to the properties below.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**manager** | **str** | Name of the secret manager handling the secret. Defaults to &#x60;cloudharness&#x60;, which creates the value in the application secret. Set explicitly to null to leave the secret unmanaged: nothing is created and the secret is assumed to exist already. | [optional] 
**default** | **str** | Value used by the &#x60;cloudharness&#x60; manager and as a fallback when the secret manager is not available, as in local docker compose deployments. Follows the same conventions as a plain secret value: null or empty generates a random value once, &#x60;?&#x60; generates a new random value at every deployment. | [optional] 

## Example

```python
from cloudharness_model.models.secret_config import SecretConfig

# TODO update the JSON string below
json = "{}"
# create an instance of SecretConfig from a JSON string
secret_config_instance = SecretConfig.from_json(json)
# print the JSON string representation of the object
print(SecretConfig.to_json())

# convert the object into a dict
secret_config_dict = secret_config_instance.to_dict()
# create an instance of SecretConfig from a dict
secret_config_from_dict = SecretConfig.from_dict(secret_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


