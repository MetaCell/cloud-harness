# InlineResponse202Task


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**href** | **str** | the url where to check the operation status | [optional] 
**name** | **str** |  | [optional] 

## Example

```python
from cloudharness_cli.samples.models.inline_response202_task import InlineResponse202Task

# TODO update the JSON string below
json = "{}"
# create an instance of InlineResponse202Task from a JSON string
inline_response202_task_instance = InlineResponse202Task.from_json(json)
# print the JSON string representation of the object
print(InlineResponse202Task.to_json())

# convert the object into a dict
inline_response202_task_dict = inline_response202_task_instance.to_dict()
# create an instance of InlineResponse202Task from a dict
inline_response202_task_from_dict = InlineResponse202Task.from_dict(inline_response202_task_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


