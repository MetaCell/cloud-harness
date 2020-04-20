# cloudharness_cli.samples.AuthApi

All URIs are relative to *https://samples.cloudharness.metacell.us/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**valid_token**](AuthApi.md#valid_token) | **GET** /valid | Check if the token is valid. Get a token by logging into the base url


# **valid_token**
> list[Valid] valid_token()

Check if the token is valid. Get a token by logging into the base url

Check if the token is valid 

### Example

* Bearer (JWT) Authentication (bearerAuth):
```python
from __future__ import print_function
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint
configuration = cloudharness_cli.samples.Configuration()
# Configure Bearer authorization (JWT): bearerAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to https://samples.cloudharness.metacell.us/api
configuration.host = "https://samples.cloudharness.metacell.us/api"

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.AuthApi(api_client)
    
    try:
        # Check if the token is valid. Get a token by logging into the base url
        api_response = api_instance.valid_token()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling AuthApi->valid_token: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[Valid]**](Valid.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Check if token is valid |  -  |
**400** | bad input parameter |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

