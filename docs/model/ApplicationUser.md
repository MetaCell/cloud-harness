# ApplicationUser

Defines a user

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**username** | **str** |  | 
**password** | **str** |  | [optional] 
**client_roles** | **List[str]** |  | [optional] 
**realm_roles** | **List[str]** |  | [optional] 

## Example

```python
from cloudharness_model.models.application_user import ApplicationUser

# TODO update the JSON string below
json = "{}"
# create an instance of ApplicationUser from a JSON string
application_user_instance = ApplicationUser.from_json(json)
# print the JSON string representation of the object
print ApplicationUser.to_json()

# convert the object into a dict
application_user_dict = application_user_instance.to_dict()
# create an instance of ApplicationUser from a dict
application_user_form_dict = application_user.from_dict(application_user_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


