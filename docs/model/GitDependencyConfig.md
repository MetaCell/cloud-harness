# GitDependencyConfig

Defines a git repo to be cloned inside the application path

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**branch_tag** | **str** |  | 
**path** | **str** | Defines the path where the repo is cloned. default: /git | [optional] 

## Example

```python
from cloudharness_model.models.git_dependency_config import GitDependencyConfig

# TODO update the JSON string below
json = "{}"
# create an instance of GitDependencyConfig from a JSON string
git_dependency_config_instance = GitDependencyConfig.from_json(json)
# print the JSON string representation of the object
print GitDependencyConfig.to_json()

# convert the object into a dict
git_dependency_config_dict = git_dependency_config_instance.to_dict()
# create an instance of GitDependencyConfig from a dict
git_dependency_config_form_dict = git_dependency_config.from_dict(git_dependency_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


