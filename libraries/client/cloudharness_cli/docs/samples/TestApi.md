# cloudharness_cli.samples.TestApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**error**](TestApi.md#error) | **GET** /error | test sentry is working
[**ping**](TestApi.md#ping) | **GET** /ping | test the application is up


# **error**
> str error()

test sentry is working

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import test_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
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
**200** | This won&#39;t happen |  -  |
**500** | Sentry entry should come! |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ping**
> float ping()

test the application is up

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import test_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
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

### Return type

**float**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | What we want |  -  |
**500** | This shouldn&#39;t happen |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

