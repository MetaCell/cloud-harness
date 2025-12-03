# ApplicationAccountsConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**roles** | **List[str]** | Specify roles to be created in this deployment specific for this application | [optional] 
**users** | [**List[ApplicationUser]**](ApplicationUser.md) | Defines test users to be added to the deployment, specific for this application | [optional] 

## Example

```python
from cloudharness_model.models.application_accounts_config import ApplicationAccountsConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ApplicationAccountsConfig from a JSON string
application_accounts_config_instance = ApplicationAccountsConfig.from_json(json)
# print the JSON string representation of the object
print(ApplicationAccountsConfig.to_json())

# convert the object into a dict
application_accounts_config_dict = application_accounts_config_instance.to_dict()
# create an instance of ApplicationAccountsConfig from a dict
application_accounts_config_from_dict = ApplicationAccountsConfig.from_dict(application_accounts_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


