# Operation

represents the status of a distributed API call
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | usually set when an error occurred | [optional] 
**name** | **str** | operation name | [optional] 
**create_time** | **datetime** |  | [optional] [readonly] 
**status** | [**OperationStatus**](OperationStatus.md) |  | [optional] 
**workflow** | **str** | low level representation as an Argo json | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


