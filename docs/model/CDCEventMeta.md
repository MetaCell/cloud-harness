# CDCEventMeta



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**app_name** | **str** | The name of the application/microservice sending the message | 
**user** | [**User**](User.md) |  | [optional] 
**args** | **List[Dict[str, object]]** | the caller function arguments | [optional] 
**kwargs** | **object** | the caller function keyword arguments | [optional] 
**description** | **str** | General description -- for human consumption | [optional] 

## Example

```python
from cloudharness_model.models.cdc_event_meta import CDCEventMeta

# TODO update the JSON string below
json = "{}"
# create an instance of CDCEventMeta from a JSON string
cdc_event_meta_instance = CDCEventMeta.from_json(json)
# print the JSON string representation of the object
print CDCEventMeta.to_json()

# convert the object into a dict
cdc_event_meta_dict = cdc_event_meta_instance.to_dict()
# create an instance of CDCEventMeta from a dict
cdc_event_meta_form_dict = cdc_event_meta.from_dict(cdc_event_meta_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


