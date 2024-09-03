# ApiTestsConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Enables api tests for this application (default: false) | 
**autotest** | **bool** | Specify whether to run the common smoke tests | 
**run_params** | **List[str]** | Additional schemathesis parameters | [optional] 
**checks** | **List[str]** | One of the Schemathesis checks:  - not_a_server_error. The response has 5xx HTTP status; - status_code_conformance. The response status is not defined in the API schema; - content_type_conformance. The response content type is not defined in the API schema; - response_schema_conformance. The response content does not conform to the schema defined for this specific response; - response_headers_conformance. The response headers does not contain all defined headers. | 

## Example

```python
from cloudharness_model.models.api_tests_config import ApiTestsConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ApiTestsConfig from a JSON string
api_tests_config_instance = ApiTestsConfig.from_json(json)
# print the JSON string representation of the object
print ApiTestsConfig.to_json()

# convert the object into a dict
api_tests_config_dict = api_tests_config_instance.to_dict()
# create an instance of ApiTestsConfig from a dict
api_tests_config_form_dict = api_tests_config.from_dict(api_tests_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


