# cloudharness_cli.workflows.model.operation.Operation

represents the status of a distributed API call

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, bool, None, list, tuple, bytes, io.FileIO, io.BufferedReader,  | frozendict.frozendict, str, decimal.Decimal, BoolClass, NoneClass, tuple, bytes, FileIO | represents the status of a distributed API call | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**message** | str,  | str,  | usually set when an error occurred | [optional] 
**name** | str,  | str,  | operation name | [optional] 
**createTime** | str, datetime,  | str,  |  | [optional] value must conform to RFC-3339 date-time
**status** | [**OperationStatus**](OperationStatus.md) | [**OperationStatus**](OperationStatus.md) |  | [optional] 
**workflow** | str,  | str,  | low level representation as an Argo json | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

