# OrchestrationEvent

A message sent to the orchestration queue. Applications can listen to these events to react to CRUD events happening on other applications.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**operation** | **str** | the operation on the object e.g. create / update / delete | 
**uid** | **str** | the unique identifier attribute of the object | 
**message_type** | **str** | the type of the message (relates to the object type) e.g. jobs | 
**meta** | [**OrchestrationEventMeta**](OrchestrationEventMeta.md) |  | 
**resource** | [**FreeObject**](FreeObject.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


