# ApplicationTestConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**unit** | [**UnitTestsConfig**](UnitTestsConfig.md) |  | 
**api** | [**ApiTestsConfig**](ApiTestsConfig.md) |  | 
**e2e** | [**E2ETestsConfig**](E2ETestsConfig.md) |  | 

## Example

```python
from cloudharness_model.models.application_test_config import ApplicationTestConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ApplicationTestConfig from a JSON string
application_test_config_instance = ApplicationTestConfig.from_json(json)
# print the JSON string representation of the object
print(ApplicationTestConfig.to_json())

# convert the object into a dict
application_test_config_dict = application_test_config_instance.to_dict()
# create an instance of ApplicationTestConfig from a dict
application_test_config_from_dict = ApplicationTestConfig.from_dict(application_test_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


