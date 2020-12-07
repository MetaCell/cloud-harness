# cloudharness_cli.samples.WorkflowsApi

All URIs are relative to *https://samples.cloudharness.metacell.us/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**error**](WorkflowsApi.md#error) | **GET** /error | test sentry is working
[**submit_async**](WorkflowsApi.md#submit_async) | **GET** /operation_async | Send an asynchronous operation
[**submit_sync**](WorkflowsApi.md#submit_sync) | **GET** /operation_sync | Send a synchronous operation
[**submit_sync_with_results**](WorkflowsApi.md#submit_sync_with_results) | **GET** /operation_sync_results | Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud


# **error**
> str error()

test sentry is working

### Example

```python
from __future__ import print_function
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.WorkflowsApi(api_client)
    
    try:
        # test sentry is working
        api_response = api_instance.error()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling WorkflowsApi->error: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

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
**500** | Sentry entry should come! |  -  |
**200** | This won&#39;t happen |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **submit_async**
> InlineResponse202 submit_async()

Send an asynchronous operation

### Example

```python
from __future__ import print_function
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.WorkflowsApi(api_client)
    
    try:
        # Send an asynchronous operation
        api_response = api_instance.submit_async()
        pprint(api_response)
    except ApiException as e:
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
> str submit_sync()

Send a synchronous operation

### Example

```python
from __future__ import print_function
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.WorkflowsApi(api_client)
    
    try:
        # Send a synchronous operation
        api_response = api_instance.submit_sync()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling WorkflowsApi->submit_sync: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

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

# **submit_sync_with_results**
> str submit_sync_with_results(a=a, b=b)

Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud

### Example

```python
from __future__ import print_function
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.WorkflowsApi(api_client)
    a = 10 # float | first number to sum (optional)
b = 10 # float | second number to sum (optional)

    try:
        # Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
        api_response = api_instance.submit_sync_with_results(a=a, b=b)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling WorkflowsApi->submit_sync_with_results: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **a** | **float**| first number to sum | [optional] 
 **b** | **float**| second number to sum | [optional] 

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

