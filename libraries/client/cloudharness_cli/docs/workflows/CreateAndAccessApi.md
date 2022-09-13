# cloudharness_cli.workflows.CreateAndAccessApi

All URIs are relative to *https://workflows.cloudharness.metacell.us/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_operation**](CreateAndAccessApi.md#delete_operation) | **DELETE** /operations/{name} | deletes operation by name
[**get_operation**](CreateAndAccessApi.md#get_operation) | **GET** /operations/{name} | get operation by name
[**list_operations**](CreateAndAccessApi.md#list_operations) | **GET** /operations | lists operations
[**log_operation**](CreateAndAccessApi.md#log_operation) | **GET** /operations/{name}/logs | get operation by name


# **delete_operation**
> delete_operation(name)

deletes operation by name

delete operation by its name 

### Example


```python
import time
import cloudharness_cli.workflows
from cloudharness_cli.workflows.api import create_and_access_api
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)
    name = "name_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        # deletes operation by name
        api_instance.delete_operation(name)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->delete_operation: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  |

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
**200** | delete OK |  -  |
**404** | not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_operation**
> [Operation] get_operation(name)

get operation by name

retrieves an operation by its name 

### Example


```python
import time
import cloudharness_cli.workflows
from cloudharness_cli.workflows.api import create_and_access_api
from cloudharness_cli.workflows.model.operation import Operation
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)
    name = "name_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        # get operation by name
        api_response = api_instance.get_operation(name)
        pprint(api_response)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->get_operation: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  |

### Return type

[**[Operation]**](Operation.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | search results matching criteria |  -  |
**404** | not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_operations**
> OperationSearchResult list_operations()

lists operations

see all operations for the user 

### Example


```python
import time
import cloudharness_cli.workflows
from cloudharness_cli.workflows.api import create_and_access_api
from cloudharness_cli.workflows.model.operation_status import OperationStatus
from cloudharness_cli.workflows.model.operation_search_result import OperationSearchResult
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)
    status = OperationStatus("QUEUED") # OperationStatus | filter by status (optional)
    previous_search_token = "previous_search_token_example" # str | continue previous search (pagination chunks) (optional)
    limit = 10 # int | maximum number of records to return per page (optional) if omitted the server will use the default value of 10

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # lists operations
        api_response = api_instance.list_operations(status=status, previous_search_token=previous_search_token, limit=limit)
        pprint(api_response)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->list_operations: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **status** | **OperationStatus**| filter by status | [optional]
 **previous_search_token** | **str**| continue previous search (pagination chunks) | [optional]
 **limit** | **int**| maximum number of records to return per page | [optional] if omitted the server will use the default value of 10

### Return type

[**OperationSearchResult**](OperationSearchResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | search results matching criteria |  -  |
**400** | bad input parameter |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **log_operation**
> str log_operation(name)

get operation by name

retrieves an operation log by its name 

### Example


```python
import time
import cloudharness_cli.workflows
from cloudharness_cli.workflows.api import create_and_access_api
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)


# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)
    name = "name_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        # get operation by name
        api_response = api_instance.log_operation(name)
        pprint(api_response)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->log_operation: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  |

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | search results matching criteria |  -  |
**404** | not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

