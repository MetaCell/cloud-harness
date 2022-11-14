# cloudharness_model.model.uri_role_mapping_config.UriRoleMappingConfig

Defines the application Gatekeeper configuration, if enabled (i.e. `secured: true`.

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  | Defines the application Gatekeeper configuration, if enabled (i.e. &#x60;secured: true&#x60;. | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**[roles](#roles)** | list, tuple,  | tuple,  | Roles allowed to access the present uri | 
**uri** | [**PathSpecifier**](PathSpecifier.md) | [**PathSpecifier**](PathSpecifier.md) |  | 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

# roles

Roles allowed to access the present uri

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Roles allowed to access the present uri | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

