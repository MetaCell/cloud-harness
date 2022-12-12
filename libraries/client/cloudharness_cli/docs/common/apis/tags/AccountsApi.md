<a name="__pageTop"></a>
# cloudharness_cli.common.apis.tags.accounts_api.AccountsApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_config**](#get_config) | **get** /accounts/config | Gets the config for logging in into accounts

# **get_config**
<a name="get_config"></a>
> {str: (bool, date, datetime, dict, float, int, list, str, none_type)} get_config()

Gets the config for logging in into accounts

Gets the config for logging in into accounts

### Example

```python
import cloudharness_cli.common
from cloudharness_cli.common.apis.tags import accounts_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.common.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.common.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = accounts_api.AccountsApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Gets the config for logging in into accounts
        api_response = api_instance.get_config()
        pprint(api_response)
    except cloudharness_cli.common.ApiException as e:
        print("Exception when calling AccountsApi->get_config: %s\n" % e)
```
### Parameters
This endpoint does not need any parameter.

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#get_config.ApiResponseFor200) | Config for accounts log in

#### get_config.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**url** | str,  | str,  | The auth URL. | [optional] 
**realm** | str,  | str,  | The realm. | [optional] 
**clientId** | str,  | str,  | The clientID. | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

