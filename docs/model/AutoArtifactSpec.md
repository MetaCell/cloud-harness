# AutoArtifactSpec



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | 
**name** | **str** |  | [optional] 

## Example

```python
from cloudharness_model.models.auto_artifact_spec import AutoArtifactSpec

# TODO update the JSON string below
json = "{}"
# create an instance of AutoArtifactSpec from a JSON string
auto_artifact_spec_instance = AutoArtifactSpec.from_json(json)
# print the JSON string representation of the object
print AutoArtifactSpec.to_json()

# convert the object into a dict
auto_artifact_spec_dict = auto_artifact_spec_instance.to_dict()
# create an instance of AutoArtifactSpec from a dict
auto_artifact_spec_form_dict = auto_artifact_spec.from_dict(auto_artifact_spec_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


