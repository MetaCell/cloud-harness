# cloudharness_cli.common.AccountsApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_config**](AccountsApi.md#get_config) | **GET** /accounts/config | Gets the config for logging in into accounts


# **get_config**
> InlineResponse200 get_config()

Gets the config for logging in into accounts

Gets the config for logging in into accounts

### Example


```python
import time
import cloudharness_cli.common
from cloudharness_cli.common.api import accounts_api
from cloudharness_cli.common.model.inline_response200 import InlineResponse200
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.common.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.common.ApiClient() as api_client:
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

### Return type

[**InlineResponse200**](InlineResponse200.md)

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

