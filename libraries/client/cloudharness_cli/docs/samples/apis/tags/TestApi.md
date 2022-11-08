<a name="__pageTop"></a>
# cloudharness_cli.samples.apis.tags.test_api.TestApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**error**](#error) | **get** /error | test sentry is working
[**ping**](#ping) | **get** /ping | test the application is up

# **error**
<a name="error"></a>
> str error()

test sentry is working

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import test_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = test_api.TestApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # test sentry is working
        api_response = api_instance.error()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling TestApi->error: %s\n" % e)
```
### Parameters
This endpoint does not need any parameter.

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#error.ApiResponseFor200) | This won&#x27;t happen
500 | [ApiResponseFor500](#error.ApiResponseFor500) | Sentry entry should come!

#### error.ApiResponseFor200
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

#### error.ApiResponseFor500
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **ping**
<a name="ping"></a>
> int, float ping()

test the application is up

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import test_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = test_api.TestApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # test the application is up
        api_response = api_instance.ping()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling TestApi->ping: %s\n" % e)
```
### Parameters
This endpoint does not need any parameter.

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#ping.ApiResponseFor200) | What we want
500 | [ApiResponseFor500](#ping.ApiResponseFor500) | This shouldn&#x27;t happen

#### ping.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
decimal.Decimal, int, float,  | decimal.Decimal,  |  | 

#### ping.ApiResponseFor500
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

