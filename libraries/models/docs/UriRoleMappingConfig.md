# UriRoleMappingConfig

Defines the application Gatekeeper configuration, if enabled (i.e. `secured: true`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** |  | 
**roles** | **List[str]** | Roles allowed to access the present uri | [optional] 
**methods** | **List[str]** | HTTP methods (uppercase) the mapping applies to. Empty means all methods. Passed through to the gatekeeper resource when &#x60;secured&#x60; is true. When &#x60;deployment.statefulset&#x60; is true, uris declaring a write method (POST/PUT/PATCH/DELETE) are also routed through the ingress to the leader service (pod 0). | [optional] 
**white_listed** | **bool** |  | [optional] 

## Example

```python
from cloudharness_model.models.uri_role_mapping_config import UriRoleMappingConfig

# TODO update the JSON string below
json = "{}"
# create an instance of UriRoleMappingConfig from a JSON string
uri_role_mapping_config_instance = UriRoleMappingConfig.from_json(json)
# print the JSON string representation of the object
print(UriRoleMappingConfig.to_json())

# convert the object into a dict
uri_role_mapping_config_dict = uri_role_mapping_config_instance.to_dict()
# create an instance of UriRoleMappingConfig from a dict
uri_role_mapping_config_from_dict = UriRoleMappingConfig.from_dict(uri_role_mapping_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


