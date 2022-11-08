<a name="__pageTop"></a>
# cloudharness_cli.samples.apis.tags.workflows_api.WorkflowsApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**submit_async**](#submit_async) | **get** /operation_async | Send an asynchronous operation
[**submit_sync**](#submit_sync) | **get** /operation_sync | Send a synchronous operation
[**submit_sync_with_results**](#submit_sync_with_results) | **get** /operation_sync_results | Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud

# **submit_async**
<a name="submit_async"></a>
> InlineResponse202 submit_async()

Send an asynchronous operation

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import workflows_api
from cloudharness_cli/samples.model.inline_response202 import InlineResponse202
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
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

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
202 | [ApiResponseFor202](#submit_async.ApiResponseFor202) | Submitted operation. See also https://restfulapi.net/http-status-202-accepted/

#### submit_async.ApiResponseFor202
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor202ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor202ResponseBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**InlineResponse202**](../../models/InlineResponse202.md) |  | 


### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **submit_sync**
<a name="submit_sync"></a>
> {str: (bool, date, datetime, dict, float, int, list, str, none_type)} submit_sync()

Send a synchronous operation

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import workflows_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
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

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#submit_sync.ApiResponseFor200) | Operation result

#### submit_sync.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **submit_sync_with_results**
<a name="submit_sync_with_results"></a>
> str submit_sync_with_results(ab)

Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import workflows_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = workflows_api.WorkflowsApi(api_client)

    # example passing only required values which don't have defaults set
    query_params = {
        'a': 10,
        'b': 10,
    }
    try:
        # Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
        api_response = api_instance.submit_sync_with_results(
            query_params=query_params,
        )
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling WorkflowsApi->submit_sync_with_results: %s\n" % e)
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
a | ASchema | | 
b | BSchema | | 


# ASchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
decimal.Decimal, int, float,  | decimal.Decimal,  |  | 

# BSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
decimal.Decimal, int, float,  | decimal.Decimal,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#submit_sync_with_results.ApiResponseFor200) | Operation result

#### submit_sync_with_results.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

