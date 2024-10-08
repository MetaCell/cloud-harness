# cloudharness_cli.common.ConfigApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_version**](ConfigApi.md#get_version) | **GET** /version | 


# **get_version**
> AppVersion get_version()



### Example


```python
import cloudharness_cli.common
from cloudharness_cli.common.models.app_version import AppVersion
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
    api_instance = cloudharness_cli.common.ConfigApi(api_client)

    try:
        api_response = api_instance.get_version()
        print("The response of ConfigApi->get_version:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfigApi->get_version: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**AppVersion**](AppVersion.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Deployment version GET |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

