# DockerfileConfig

Configuration for a dockerfile

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**build_args** | **Dict[str, object]** |  | [optional] 

## Example

```python
from cloudharness_model.models.dockerfile_config import DockerfileConfig

# TODO update the JSON string below
json = "{}"
# create an instance of DockerfileConfig from a JSON string
dockerfile_config_instance = DockerfileConfig.from_json(json)
# print the JSON string representation of the object
print DockerfileConfig.to_json()

# convert the object into a dict
dockerfile_config_dict = dockerfile_config_instance.to_dict()
# create an instance of DockerfileConfig from a dict
dockerfile_config_form_dict = dockerfile_config.from_dict(dockerfile_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


