# cloudharness_model.model.api_tests_config.ApiTestsConfig

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**[checks](#checks)** | list, tuple,  | tuple,  | One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers. | 
**autotest** | bool,  | BoolClass,  | Specify whether to run the common smoke tests | 
**enabled** | bool,  | BoolClass,  | Enables api tests for this application (default: false) | 
**[runParams](#runParams)** | list, tuple,  | tuple,  | Additional schemathesis parameters | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

# checks

One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers.

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers. | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

# runParams

Additional schemathesis parameters

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Additional schemathesis parameters | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

