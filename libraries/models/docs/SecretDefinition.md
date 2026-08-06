# SecretDefinition

An application secret, defined either as a plain value or as a secret configuration object. A `string` (or null) is the secret value itself: empty or null generates a random value, `?` generates a new random value at every deployment. A `SecretConfig` object instead delegates the secret to a secret manager, and carries the settings that manager needs.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**manager** | **str** | Name of the secret manager handling the secret. Defaults to &#x60;cloudharness&#x60;, which creates the value in the application secret. Set explicitly to null to leave the secret unmanaged: nothing is created and the secret is assumed to exist already. | [optional] 
**default** | **str** | Value used by the &#x60;cloudharness&#x60; manager and as a fallback when the secret manager is not available, as in local docker compose deployments. Follows the same conventions as a plain secret value: null or empty generates a random value once, &#x60;?&#x60; generates a new random value at every deployment. | [optional] 

## Example

```python
from cloudharness_model.models.secret_definition import SecretDefinition

# TODO update the JSON string below
json = "{}"
# create an instance of SecretDefinition from a JSON string
secret_definition_instance = SecretDefinition.from_json(json)
# print the JSON string representation of the object
print(SecretDefinition.to_json())

# convert the object into a dict
secret_definition_dict = secret_definition_instance.to_dict()
# create an instance of SecretDefinition from a dict
secret_definition_from_dict = SecretDefinition.from_dict(secret_definition_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


