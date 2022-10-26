# cloudharness_cli.common.SentryApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getdsn**](SentryApi.md#getdsn) | **GET** /sentry/getdsn/{appname} | Gets the Sentry DSN for a given application


# **getdsn**
> str getdsn(appname)

Gets the Sentry DSN for a given application

Gets the Sentry DSN for a given application

### Example


```python
import time
import cloudharness_cli.common
from cloudharness_cli.common.api import sentry_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.common.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.common.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = sentry_api.SentryApi(api_client)
    appname = "appname_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        # Gets the Sentry DSN for a given application
        api_response = api_instance.getdsn(appname)
        pprint(api_response)
    except cloudharness_cli.common.ApiException as e:
        print("Exception when calling SentryApi->getdsn: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **appname** | **str**|  |

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Sentry DSN for the given application |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

