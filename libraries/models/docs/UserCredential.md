# UserCredential


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_date** | **int** |  | [optional] 
**credential_data** | **str** |  | [optional] 
**id** | **str** |  | [optional] 
**priority** | **int** |  | [optional] 
**secret_data** | **str** |  | [optional] 
**temporary** | **bool** |  | [optional] 
**type** | **str** |  | [optional] 
**user_label** | **str** |  | [optional] 
**value** | **str** |  | [optional] 

## Example

```python
from cloudharness_model.models.user_credential import UserCredential

# TODO update the JSON string below
json = "{}"
# create an instance of UserCredential from a JSON string
user_credential_instance = UserCredential.from_json(json)
# print the JSON string representation of the object
print(UserCredential.to_json())

# convert the object into a dict
user_credential_dict = user_credential_instance.to_dict()
# create an instance of UserCredential from a dict
user_credential_from_dict = UserCredential.from_dict(user_credential_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


