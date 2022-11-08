# ApiTestsConfig


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Enables api tests for this application (default: false) | 
**autotest** | **bool** | Specify whether to run the common smoke tests | 
**checks** | **[str]** | One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers. | 
**run_params** | **[str]** | Additional schemathesis parameters | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


