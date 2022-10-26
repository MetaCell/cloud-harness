# cloudharness_cli.samples.AuthApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**valid_cookie**](AuthApi.md#valid_cookie) | **GET** /valid-cookie | Check if the token is valid. Get a token by logging into the base url
[**valid_token**](AuthApi.md#valid_token) | **GET** /valid | Check if the token is valid. Get a token by logging into the base url


# **valid_cookie**
> str valid_cookie()

Check if the token is valid. Get a token by logging into the base url

Check if the token is valid 

### Example

* Api Key Authentication (cookieAuth):

```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import auth_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = auth_api.AuthApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Check if the token is valid. Get a token by logging into the base url
        api_response = api_instance.valid_cookie()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling AuthApi->valid_cookie: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

**str**

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Check if token is valid |  -  |
**401** | invalid token, unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **valid_token**
> str valid_token()

Check if the token is valid. Get a token by logging into the base url

Check if the token is valid 

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import auth_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = cloudharness_cli.samples.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = auth_api.AuthApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Check if the token is valid. Get a token by logging into the base url
        api_response = api_instance.valid_token()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling AuthApi->valid_token: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

**str**

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Check if token is valid |  -  |
**401** | invalid token, unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

