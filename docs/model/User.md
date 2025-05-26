# User


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access** | **Dict[str, object]** |  | [optional] 
**attributes** | **Dict[str, object]** |  | [optional] 
**client_roles** | **Dict[str, object]** |  | [optional] 
**created_timestamp** | **int** |  | [optional] 
**credentials** | [**List[UserCredential]**](UserCredential.md) |  | [optional] 
**disableable_credential_types** | **List[str]** |  | [optional] 
**email** | **str** |  | [optional] 
**email_verified** | **bool** |  | [optional] 
**enabled** | **bool** |  | [optional] 
**federation_link** | **str** |  | [optional] 
**first_name** | **str** |  | [optional] 
**groups** | **List[str]** |  | [optional] 
**id** | **str** |  | [optional] 
**last_name** | **str** |  | [optional] 
**realm_roles** | **List[str]** |  | [optional] 
**required_actions** | **List[str]** |  | [optional] 
**service_account_client_id** | **str** |  | [optional] 
**username** | **str** |  | [optional] 
**additional_properties** | **object** |  | [optional] 

## Example

```python
from cloudharness_model.models.user import User

# TODO update the JSON string below
json = "{}"
# create an instance of User from a JSON string
user_instance = User.from_json(json)
# print the JSON string representation of the object
print(User.to_json())

# convert the object into a dict
user_dict = user_instance.to_dict()
# create an instance of User from a dict
user_from_dict = User.from_dict(user_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


