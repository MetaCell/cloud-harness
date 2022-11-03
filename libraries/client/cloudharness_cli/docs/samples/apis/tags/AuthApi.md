<a name="__pageTop"></a>
# cloudharness_cli.samples.apis.tags.auth_api.AuthApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**valid_cookie**](#valid_cookie) | **get** /valid-cookie | Check if the token is valid. Get a token by logging into the base url
[**valid_token**](#valid_token) | **get** /valid | Check if the token is valid. Get a token by logging into the base url

# **valid_cookie**
<a name="valid_cookie"></a>
> str valid_cookie()

Check if the token is valid. Get a token by logging into the base url

Check if the token is valid 

### Example

* Api Key Authentication (cookieAuth):
```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import auth_api
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

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#valid_cookie.ApiResponseFor200) | Check if token is valid
401 | [ApiResponseFor401](#valid_cookie.ApiResponseFor401) | invalid token, unauthorized

#### valid_cookie.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

#### valid_cookie.ApiResponseFor401
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

[cookieAuth](../../../README.md#cookieAuth)

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **valid_token**
<a name="valid_token"></a>
> str valid_token()

Check if the token is valid. Get a token by logging into the base url

Check if the token is valid 

### Example

* Bearer (JWT) Authentication (bearerAuth):
```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import auth_api
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

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#valid_token.ApiResponseFor200) | Check if token is valid
401 | [ApiResponseFor401](#valid_token.ApiResponseFor401) | invalid token, unauthorized

#### valid_token.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

#### valid_token.ApiResponseFor401
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

[bearerAuth](../../../README.md#bearerAuth)

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

