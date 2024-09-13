# OperationSearchResult

a list of operations with meta data about the result

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**meta** | [**SearchResultData**](SearchResultData.md) |  | [optional] 
**items** | [**List[Operation]**](Operation.md) |  | [optional] 

## Example

```python
from cloudharness_cli.workflows.models.operation_search_result import OperationSearchResult

# TODO update the JSON string below
json = "{}"
# create an instance of OperationSearchResult from a JSON string
operation_search_result_instance = OperationSearchResult.from_json(json)
# print the JSON string representation of the object
print(OperationSearchResult.to_json())

# convert the object into a dict
operation_search_result_dict = operation_search_result_instance.to_dict()
# create an instance of OperationSearchResult from a dict
operation_search_result_from_dict = OperationSearchResult.from_dict(operation_search_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


