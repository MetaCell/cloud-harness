# cloudharness_cli.samples.WorkflowsApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**submit_async**](WorkflowsApi.md#submit_async) | **GET** /operation_async | Send an asynchronous operation
[**submit_sync**](WorkflowsApi.md#submit_sync) | **GET** /operation_sync | Send a synchronous operation
[**submit_sync_with_results**](WorkflowsApi.md#submit_sync_with_results) | **GET** /operation_sync_results | Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud


# **submit_async**
> InlineResponse202 submit_async()

Send an asynchronous operation

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import workflows_api
from cloudharness_cli.samples.model.inline_response202 import InlineResponse202
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = workflows_api.WorkflowsApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Send an asynchronous operation
        api_response = api_instance.submit_async()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling WorkflowsApi->submit_async: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

[**InlineResponse202**](InlineResponse202.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Submitted operation. See also https://restfulapi.net/http-status-202-accepted/ |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **submit_sync**
> {str: (bool, date, datetime, dict, float, int, list, str, none_type)} submit_sync()

Send a synchronous operation

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import workflows_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = workflows_api.WorkflowsApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Send a synchronous operation
        api_response = api_instance.submit_sync()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling WorkflowsApi->submit_sync: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

**{str: (bool, date, datetime, dict, float, int, list, str, none_type)}**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Operation result |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **submit_sync_with_results**
> str submit_sync_with_results(a, b)

Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import workflows_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = workflows_api.WorkflowsApi(api_client)
    a = 10 # float | first number to sum
    b = 10 # float | second number to sum

    # example passing only required values which don't have defaults set
    try:
        # Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
        api_response = api_instance.submit_sync_with_results(a, b)
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling WorkflowsApi->submit_sync_with_results: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **a** | **float**| first number to sum |
 **b** | **float**| second number to sum |

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
**200** | Operation result |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

