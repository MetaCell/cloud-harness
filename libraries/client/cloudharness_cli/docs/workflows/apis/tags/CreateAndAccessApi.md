<a name="__pageTop"></a>
# cloudharness_cli.workflows.apis.tags.create_and_access_api.CreateAndAccessApi

All URIs are relative to *https://workflows.cloudharness.metacell.us/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_operation**](#delete_operation) | **delete** /operations/{name} | deletes operation by name
[**get_operation**](#get_operation) | **get** /operations/{name} | get operation by name
[**list_operations**](#list_operations) | **get** /operations | lists operations
[**log_operation**](#log_operation) | **get** /operations/{name}/logs | get operation by name

# **delete_operation**
<a name="delete_operation"></a>
> delete_operation(name)

deletes operation by name

delete operation by its name 

### Example

```python
import cloudharness_cli.workflows
from cloudharness_cli.workflows.apis.tags import create_and_access_api
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'name': "name_example",
    }
    try:
        # deletes operation by name
        api_response = api_instance.delete_operation(
            path_params=path_params,
        )
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->delete_operation: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
path_params | RequestPathParams | |
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### path_params
#### RequestPathParams

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
name | NameSchema | | 

# NameSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#delete_operation.ApiResponseFor200) | delete OK
404 | [ApiResponseFor404](#delete_operation.ApiResponseFor404) | not found

#### delete_operation.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### delete_operation.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **get_operation**
<a name="get_operation"></a>
> [Operation] get_operation(name)

get operation by name

retrieves an operation by its name 

### Example

```python
import cloudharness_cli.workflows
from cloudharness_cli.workflows.apis.tags import create_and_access_api
from cloudharness_cli/workflows.model.operation import Operation
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'name': "name_example",
    }
    try:
        # get operation by name
        api_response = api_instance.get_operation(
            path_params=path_params,
        )
        pprint(api_response)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->get_operation: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
path_params | RequestPathParams | |
accept_content_types | typing.Tuple[str] | default is ('application/json', ) | Tells the server the content type(s) that are accepted by the client
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### path_params
#### RequestPathParams

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
name | NameSchema | | 

# NameSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#get_operation.ApiResponseFor200) | search results matching criteria
404 | [ApiResponseFor404](#get_operation.ApiResponseFor404) | not found

#### get_operation.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  |  | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
[**Operation**]({{complexTypePrefix}}Operation.md) | [**Operation**]({{complexTypePrefix}}Operation.md) | [**Operation**]({{complexTypePrefix}}Operation.md) |  | 

#### get_operation.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **list_operations**
<a name="list_operations"></a>
> OperationSearchResult list_operations()

lists operations

see all operations for the user 

### Example

```python
import cloudharness_cli.workflows
from cloudharness_cli.workflows.apis.tags import create_and_access_api
from cloudharness_cli/workflows.model.operation_search_result import OperationSearchResult
from cloudharness_cli/workflows.model.operation_status import OperationStatus
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)

    # example passing only optional values
    query_params = {
        'status': OperationStatus("QUEUED"),
        'previous_search_token': "previous_search_token_example",
        'limit': 10,
    }
    try:
        # lists operations
        api_response = api_instance.list_operations(
            query_params=query_params,
        )
        pprint(api_response)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->list_operations: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
query_params | RequestQueryParams | |
accept_content_types | typing.Tuple[str] | default is ('application/json', ) | Tells the server the content type(s) that are accepted by the client
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### query_params
#### RequestQueryParams

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
status | StatusSchema | | optional
previous_search_token | PreviousSearchTokenSchema | | optional
limit | LimitSchema | | optional


# StatusSchema
Type | Description  | Notes
------------- | ------------- | -------------
[**OperationStatus**](../../models/OperationStatus.md) |  | 


# PreviousSearchTokenSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

# LimitSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
decimal.Decimal, int,  | decimal.Decimal,  |  | if omitted the server will use the default value of 10

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#list_operations.ApiResponseFor200) | search results matching criteria
400 | [ApiResponseFor400](#list_operations.ApiResponseFor400) | bad input parameter

#### list_operations.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**OperationSearchResult**](../../models/OperationSearchResult.md) |  | 


#### list_operations.ApiResponseFor400
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **log_operation**
<a name="log_operation"></a>
> str log_operation(name)

get operation by name

retrieves an operation log by its name 

### Example

```python
import cloudharness_cli.workflows
from cloudharness_cli.workflows.apis.tags import create_and_access_api
from pprint import pprint
# Defining the host is optional and defaults to https://workflows.cloudharness.metacell.us/api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.workflows.Configuration(
    host = "https://workflows.cloudharness.metacell.us/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = create_and_access_api.CreateAndAccessApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'name': "name_example",
    }
    try:
        # get operation by name
        api_response = api_instance.log_operation(
            path_params=path_params,
        )
        pprint(api_response)
    except cloudharness_cli.workflows.ApiException as e:
        print("Exception when calling CreateAndAccessApi->log_operation: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
path_params | RequestPathParams | |
accept_content_types | typing.Tuple[str] | default is ('text/plain', ) | Tells the server the content type(s) that are accepted by the client
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### path_params
#### RequestPathParams

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
name | NameSchema | | 

# NameSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#log_operation.ApiResponseFor200) | search results matching criteria
404 | [ApiResponseFor404](#log_operation.ApiResponseFor404) | not found

#### log_operation.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyTextPlain, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyTextPlain

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

#### log_operation.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

