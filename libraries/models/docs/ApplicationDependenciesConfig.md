# ApplicationDependenciesConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**hard** | **List[str]** | Hard dependencies indicate that the application may not start without these other applications. | [optional] 
**soft** | **List[str]** | Soft dependencies indicate that the application will work partially without these other applications. | [optional] 
**build** | **List[str]** | Hard dependencies indicate that the application Docker image build requires these base/common images | [optional] 
**git** | [**List[GitDependencyConfig]**](GitDependencyConfig.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.application_dependencies_config import ApplicationDependenciesConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ApplicationDependenciesConfig from a JSON string
application_dependencies_config_instance = ApplicationDependenciesConfig.from_json(json)
# print the JSON string representation of the object
print(ApplicationDependenciesConfig.to_json())

# convert the object into a dict
application_dependencies_config_dict = application_dependencies_config_instance.to_dict()
# create an instance of ApplicationDependenciesConfig from a dict
application_dependencies_config_from_dict = ApplicationDependenciesConfig.from_dict(application_dependencies_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


