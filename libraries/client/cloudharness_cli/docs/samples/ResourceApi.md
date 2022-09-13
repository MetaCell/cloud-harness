# cloudharness_cli.samples.ResourceApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_sample_resource**](ResourceApi.md#create_sample_resource) | **POST** /sampleresources | Create a SampleResource
[**delete_sample_resource**](ResourceApi.md#delete_sample_resource) | **DELETE** /sampleresources/{sampleresourceId} | Delete a SampleResource
[**get_sample_resource**](ResourceApi.md#get_sample_resource) | **GET** /sampleresources/{sampleresourceId} | Get a SampleResource
[**get_sample_resources**](ResourceApi.md#get_sample_resources) | **GET** /sampleresources | List All SampleResources
[**update_sample_resource**](ResourceApi.md#update_sample_resource) | **PUT** /sampleresources/{sampleresourceId} | Update a SampleResource


# **create_sample_resource**
> create_sample_resource(sample_resource)

Create a SampleResource

Creates a new instance of a `SampleResource`.

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import resource_api
from cloudharness_cli.samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)
    sample_resource = SampleResource(
        a=3.14,
        b=3.14,
        id=3.14,
    ) # SampleResource | A new `SampleResource` to be created.

    # example passing only required values which don't have defaults set
    try:
        # Create a SampleResource
        api_instance.create_sample_resource(sample_resource)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->create_sample_resource: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sample_resource** | [**SampleResource**](SampleResource.md)| A new &#x60;SampleResource&#x60; to be created. |

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful response. |  -  |
**400** | Payload must be of type SampleResource |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_sample_resource**
> delete_sample_resource(sampleresource_id)

Delete a SampleResource

Deletes an existing `SampleResource`.

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import resource_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)
    sampleresource_id = "sampleresourceId_example" # str | A unique identifier for a `SampleResource`.

    # example passing only required values which don't have defaults set
    try:
        # Delete a SampleResource
        api_instance.delete_sample_resource(sampleresource_id)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->delete_sample_resource: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sampleresource_id** | **str**| A unique identifier for a &#x60;SampleResource&#x60;. |

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Successful response. |  -  |
**400** | Parameter must be integer |  -  |
**404** | Resource not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_sample_resource**
> SampleResource get_sample_resource(sampleresource_id)

Get a SampleResource

Gets the details of a single instance of a `SampleResource`.

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import resource_api
from cloudharness_cli.samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)
    sampleresource_id = "sampleresourceId_example" # str | A unique identifier for a `SampleResource`.

    # example passing only required values which don't have defaults set
    try:
        # Get a SampleResource
        api_response = api_instance.get_sample_resource(sampleresource_id)
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->get_sample_resource: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sampleresource_id** | **str**| A unique identifier for a &#x60;SampleResource&#x60;. |

### Return type

[**SampleResource**](SampleResource.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful response - returns a single &#x60;SampleResource&#x60;. |  -  |
**400** | Parameter must be integer |  -  |
**404** | Resource not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_sample_resources**
> [SampleResource] get_sample_resources()

List All SampleResources

Gets a list of all `SampleResource` entities.

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import resource_api
from cloudharness_cli.samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # List All SampleResources
        api_response = api_instance.get_sample_resources()
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->get_sample_resources: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

[**[SampleResource]**](SampleResource.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful response - returns an array of &#x60;SampleResource&#x60; entities. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_sample_resource**
> update_sample_resource(sampleresource_id, sample_resource)

Update a SampleResource

Updates an existing `SampleResource`.

### Example


```python
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.api import resource_api
from cloudharness_cli.samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)
    sampleresource_id = "sampleresourceId_example" # str | A unique identifier for a `SampleResource`.
    sample_resource = SampleResource(
        a=3.14,
        b=3.14,
        id=3.14,
    ) # SampleResource | Updated `SampleResource` information.

    # example passing only required values which don't have defaults set
    try:
        # Update a SampleResource
        api_instance.update_sample_resource(sampleresource_id, sample_resource)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->update_sample_resource: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sampleresource_id** | **str**| A unique identifier for a &#x60;SampleResource&#x60;. |
 **sample_resource** | [**SampleResource**](SampleResource.md)| Updated &#x60;SampleResource&#x60; information. |

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Successful response. |  -  |
**400** | Parameter must be integer, payload must be of type SampleResource |  -  |
**404** | Resource not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

