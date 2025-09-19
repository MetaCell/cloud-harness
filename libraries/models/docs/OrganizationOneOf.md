# OrganizationOneOf


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**domains** | [**List[NamedObject]**](NamedObject.md) |  | [optional] 
**alias** | **str** |  | [optional] 
**enabled** | **bool** |  | [optional] 
**id** | **str** |  | [optional] 

## Example

```python
from cloudharness_model.models.organization_one_of import OrganizationOneOf

# TODO update the JSON string below
json = "{}"
# create an instance of OrganizationOneOf from a JSON string
organization_one_of_instance = OrganizationOneOf.from_json(json)
# print the JSON string representation of the object
print(OrganizationOneOf.to_json())

# convert the object into a dict
organization_one_of_dict = organization_one_of_instance.to_dict()
# create an instance of OrganizationOneOf from a dict
organization_one_of_from_dict = OrganizationOneOf.from_dict(organization_one_of_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


