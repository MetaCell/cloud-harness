# cloudharness_model.model.cdc_event.CDCEvent

A message sent to the orchestration queue. Applications can listen to these events to react to data change events happening on other applications.

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  | A message sent to the orchestration queue. Applications can listen to these events to react to data change events happening on other applications. | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**uid** | str,  | str,  | the unique identifier attribute of the object | 
**meta** | [**CDCEventMeta**](CDCEventMeta.md) | [**CDCEventMeta**](CDCEventMeta.md) |  | 
**message_type** | str,  | str,  | the type of the message (relates to the object type) e.g. jobs | 
**operation** | str,  | str,  | the operation on the object e.g. create / update / delete | must be one of ["create", "update", "delete", "other", ] 
**resource** | [**FreeObject**](FreeObject.md) | [**FreeObject**](FreeObject.md) |  | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

