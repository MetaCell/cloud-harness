# cloudharness_cli.common.AccountsApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_config**](AccountsApi.md#get_config) | **GET** /accounts/config | Gets the config for logging in into accounts


# **get_config**
> GetConfig200Response get_config()

Gets the config for logging in into accounts

Gets the config for logging in into accounts

### Example


```python
import cloudharness_cli.common
from cloudharness_cli.common.models.get_config200_response import GetConfig200Response
from cloudharness_cli.common.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.common.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.common.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.common.AccountsApi(api_client)

    try:
        # Gets the config for logging in into accounts
        api_response = api_instance.get_config()
        print("The response of AccountsApi->get_config:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AccountsApi->get_config: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetConfig200Response**](GetConfig200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Config for accounts log in |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

