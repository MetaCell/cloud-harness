# CDCEvent

A message sent to the orchestration queue. Applications can listen to these events to react to data change events happening on other applications.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**operation** | **str** | the operation on the object e.g. create / update / delete | 
**uid** | **str** | the unique identifier attribute of the object | 
**message_type** | **str** | the type of the message (relates to the object type) e.g. jobs | 
**resource** | **Dict[str, object]** |  | [optional] 
**meta** | [**CDCEventMeta**](CDCEventMeta.md) |  | 

## Example

```python
from cloudharness_model.models.cdc_event import CDCEvent

# TODO update the JSON string below
json = "{}"
# create an instance of CDCEvent from a JSON string
cdc_event_instance = CDCEvent.from_json(json)
# print the JSON string representation of the object
print(CDCEvent.to_json())

# convert the object into a dict
cdc_event_dict = cdc_event_instance.to_dict()
# create an instance of CDCEvent from a dict
cdc_event_from_dict = CDCEvent.from_dict(cdc_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


