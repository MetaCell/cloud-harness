# cloudharness_cli.common.SentryApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getdsn**](SentryApi.md#getdsn) | **GET** /sentry/getdsn/{appname} | Gets the Sentry DSN for a given application


# **getdsn**
> object getdsn(appname)

Gets the Sentry DSN for a given application

Gets the Sentry DSN for a given application

### Example


```python
import cloudharness_cli.common
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
    api_instance = cloudharness_cli.common.SentryApi(api_client)
    appname = 'appname_example' # str | 

    try:
        # Gets the Sentry DSN for a given application
        api_response = api_instance.getdsn(appname)
        print("The response of SentryApi->getdsn:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SentryApi->getdsn: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **appname** | **str**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json, text/html, application/problem+json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Sentry DSN for the given application |  -  |
**400** | Sentry not configured for the given application |  -  |
**404** | Sentry not configured for the given application |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

