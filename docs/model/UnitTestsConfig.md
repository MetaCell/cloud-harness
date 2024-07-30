# UnitTestsConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Enables unit tests for this application (default: true) | 
**commands** | **List[str]** | Commands to run unit tests | 

## Example

```python
from cloudharness_model.models.unit_tests_config import UnitTestsConfig

# TODO update the JSON string below
json = "{}"
# create an instance of UnitTestsConfig from a JSON string
unit_tests_config_instance = UnitTestsConfig.from_json(json)
# print the JSON string representation of the object
print UnitTestsConfig.to_json()

# convert the object into a dict
unit_tests_config_dict = unit_tests_config_instance.to_dict()
# create an instance of UnitTestsConfig from a dict
unit_tests_config_form_dict = unit_tests_config.from_dict(unit_tests_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


