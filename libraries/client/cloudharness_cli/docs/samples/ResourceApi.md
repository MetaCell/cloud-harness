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
import cloudharness_cli.samples
from cloudharness_cli.samples.models.sample_resource import SampleResource
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.ResourceApi(api_client)
    sample_resource = cloudharness_cli.samples.SampleResource() # SampleResource | A new `SampleResource` to be created.

    try:
        # Create a SampleResource
        api_instance.create_sample_resource(sample_resource)
    except Exception as e:
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
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.ResourceApi(api_client)
    sampleresource_id = 'sampleresource_id_example' # str | A unique identifier for a `SampleResource`.

    try:
        # Delete a SampleResource
        api_instance.delete_sample_resource(sampleresource_id)
    except Exception as e:
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
import cloudharness_cli.samples
from cloudharness_cli.samples.models.sample_resource import SampleResource
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.ResourceApi(api_client)
    sampleresource_id = 'sampleresource_id_example' # str | A unique identifier for a `SampleResource`.

    try:
        # Get a SampleResource
        api_response = api_instance.get_sample_resource(sampleresource_id)
        print("The response of ResourceApi->get_sample_resource:\n")
        pprint(api_response)
    except Exception as e:
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
> List[SampleResource] get_sample_resources()

List All SampleResources

Gets a list of all `SampleResource` entities.

### Example


```python
import cloudharness_cli.samples
from cloudharness_cli.samples.models.sample_resource import SampleResource
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.ResourceApi(api_client)

    try:
        # List All SampleResources
        api_response = api_instance.get_sample_resources()
        print("The response of ResourceApi->get_sample_resources:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ResourceApi->get_sample_resources: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[SampleResource]**](SampleResource.md)

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
import cloudharness_cli.samples
from cloudharness_cli.samples.models.sample_resource import SampleResource
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.ResourceApi(api_client)
    sampleresource_id = 'sampleresource_id_example' # str | A unique identifier for a `SampleResource`.
    sample_resource = cloudharness_cli.samples.SampleResource() # SampleResource | Updated `SampleResource` information.

    try:
        # Update a SampleResource
        api_instance.update_sample_resource(sampleresource_id, sample_resource)
    except Exception as e:
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

