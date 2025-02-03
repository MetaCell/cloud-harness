# UserGroup


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access** | **Dict[str, object]** |  | [optional] 
**attributes** | **Dict[str, object]** |  | [optional] 
**client_roles** | **Dict[str, object]** |  | [optional] 
**id** | **str** |  | [optional] 
**name** | **str** |  | [optional] 
**path** | **str** |  | [optional] 
**realm_roles** | **List[str]** |  | [optional] 
**sub_groups** | [**List[UserGroup]**](UserGroup.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.user_group import UserGroup

# TODO update the JSON string below
json = "{}"
# create an instance of UserGroup from a JSON string
user_group_instance = UserGroup.from_json(json)
# print the JSON string representation of the object
print UserGroup.to_json()

# convert the object into a dict
user_group_dict = user_group_instance.to_dict()
# create an instance of UserGroup from a dict
user_group_form_dict = user_group.from_dict(user_group_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


