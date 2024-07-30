# E2ETestsConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Enables end to end testing for this application (default: false) | 
**smoketest** | **bool** | Specify whether to run the common smoke tests | 
**ignore_console_errors** | **bool** |  | [optional] 
**ignore_request_errors** | **bool** |  | [optional] 

## Example

```python
from cloudharness_model.models.e2_e_tests_config import E2ETestsConfig

# TODO update the JSON string below
json = "{}"
# create an instance of E2ETestsConfig from a JSON string
e2_e_tests_config_instance = E2ETestsConfig.from_json(json)
# print the JSON string representation of the object
print E2ETestsConfig.to_json()

# convert the object into a dict
e2_e_tests_config_dict = e2_e_tests_config_instance.to_dict()
# create an instance of E2ETestsConfig from a dict
e2_e_tests_config_form_dict = e2_e_tests_config.from_dict(e2_e_tests_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


