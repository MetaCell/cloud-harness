# SearchResultData

describes a search

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**continue_token** | **str** | token to use for pagination | [optional] 

## Example

```python
from cloudharness_cli.workflows.models.search_result_data import SearchResultData

# TODO update the JSON string below
json = "{}"
# create an instance of SearchResultData from a JSON string
search_result_data_instance = SearchResultData.from_json(json)
# print the JSON string representation of the object
print(SearchResultData.to_json())

# convert the object into a dict
search_result_data_dict = search_result_data_instance.to_dict()
# create an instance of SearchResultData from a dict
search_result_data_from_dict = SearchResultData.from_dict(search_result_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


