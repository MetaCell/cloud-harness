<a name="__pageTop"></a>
# cloudharness_cli.samples.apis.tags.resource_api.ResourceApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_sample_resource**](#create_sample_resource) | **post** /sampleresources | Create a SampleResource
[**delete_sample_resource**](#delete_sample_resource) | **delete** /sampleresources/{sampleresourceId} | Delete a SampleResource
[**get_sample_resource**](#get_sample_resource) | **get** /sampleresources/{sampleresourceId} | Get a SampleResource
[**get_sample_resources**](#get_sample_resources) | **get** /sampleresources | List All SampleResources
[**update_sample_resource**](#update_sample_resource) | **put** /sampleresources/{sampleresourceId} | Update a SampleResource

# **create_sample_resource**
<a name="create_sample_resource"></a>
> create_sample_resource(sample_resource)

Create a SampleResource

Creates a new instance of a `SampleResource`.

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import resource_api
from cloudharness_cli/samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)

    # example passing only required values which don't have defaults set
    body = SampleResource(
        a=3.14,
        b=3.14,
        id=3.14,
    )
    try:
        # Create a SampleResource
        api_response = api_instance.create_sample_resource(
            body=body,
        )
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->create_sample_resource: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
body | typing.Union[SchemaForRequestBodyApplicationJson] | required |
content_type | str | optional, default is 'application/json' | Selects the schema and serialization of the request body
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### body

# SchemaForRequestBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**SampleResource**](../../models/SampleResource.md) |  | 


### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
201 | [ApiResponseFor201](#create_sample_resource.ApiResponseFor201) | Successful response.
400 | [ApiResponseFor400](#create_sample_resource.ApiResponseFor400) | Payload must be of type SampleResource

#### create_sample_resource.ApiResponseFor201
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### create_sample_resource.ApiResponseFor400
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **delete_sample_resource**
<a name="delete_sample_resource"></a>
> delete_sample_resource(sampleresource_id)

Delete a SampleResource

Deletes an existing `SampleResource`.

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import resource_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'sampleresourceId': "sampleresourceId_example",
    }
    try:
        # Delete a SampleResource
        api_response = api_instance.delete_sample_resource(
            path_params=path_params,
        )
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->delete_sample_resource: %s\n" % e)
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
sampleresourceId | SampleresourceIdSchema | | 

# SampleresourceIdSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
204 | [ApiResponseFor204](#delete_sample_resource.ApiResponseFor204) | Successful response.
400 | [ApiResponseFor400](#delete_sample_resource.ApiResponseFor400) | Parameter must be integer
404 | [ApiResponseFor404](#delete_sample_resource.ApiResponseFor404) | Resource not found

#### delete_sample_resource.ApiResponseFor204
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### delete_sample_resource.ApiResponseFor400
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### delete_sample_resource.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **get_sample_resource**
<a name="get_sample_resource"></a>
> SampleResource get_sample_resource(sampleresource_id)

Get a SampleResource

Gets the details of a single instance of a `SampleResource`.

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import resource_api
from cloudharness_cli/samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'sampleresourceId': "sampleresourceId_example",
    }
    try:
        # Get a SampleResource
        api_response = api_instance.get_sample_resource(
            path_params=path_params,
        )
        pprint(api_response)
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->get_sample_resource: %s\n" % e)
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
sampleresourceId | SampleresourceIdSchema | | 

# SampleresourceIdSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#get_sample_resource.ApiResponseFor200) | Successful response - returns a single &#x60;SampleResource&#x60;.
400 | [ApiResponseFor400](#get_sample_resource.ApiResponseFor400) | Parameter must be integer
404 | [ApiResponseFor404](#get_sample_resource.ApiResponseFor404) | Resource not found

#### get_sample_resource.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**SampleResource**](../../models/SampleResource.md) |  | 


#### get_sample_resource.ApiResponseFor400
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### get_sample_resource.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **get_sample_resources**
<a name="get_sample_resources"></a>
> [SampleResource] get_sample_resources()

List All SampleResources

Gets a list of all `SampleResource` entities.

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import resource_api
from cloudharness_cli/samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
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

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#get_sample_resources.ApiResponseFor200) | Successful response - returns an array of &#x60;SampleResource&#x60; entities.

#### get_sample_resources.ApiResponseFor200
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
[**SampleResource**]({{complexTypePrefix}}SampleResource.md) | [**SampleResource**]({{complexTypePrefix}}SampleResource.md) | [**SampleResource**]({{complexTypePrefix}}SampleResource.md) |  | 

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **update_sample_resource**
<a name="update_sample_resource"></a>
> update_sample_resource(sampleresource_idsample_resource)

Update a SampleResource

Updates an existing `SampleResource`.

### Example

```python
import cloudharness_cli.samples
from cloudharness_cli.samples.apis.tags import resource_api
from cloudharness_cli/samples.model.sample_resource import SampleResource
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.samples.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = resource_api.ResourceApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'sampleresourceId': "sampleresourceId_example",
    }
    body = SampleResource(
        a=3.14,
        b=3.14,
        id=3.14,
    )
    try:
        # Update a SampleResource
        api_response = api_instance.update_sample_resource(
            path_params=path_params,
            body=body,
        )
    except cloudharness_cli.samples.ApiException as e:
        print("Exception when calling ResourceApi->update_sample_resource: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
body | typing.Union[SchemaForRequestBodyApplicationJson] | required |
path_params | RequestPathParams | |
content_type | str | optional, default is 'application/json' | Selects the schema and serialization of the request body
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### body

# SchemaForRequestBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**SampleResource**](../../models/SampleResource.md) |  | 


### path_params
#### RequestPathParams

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
sampleresourceId | SampleresourceIdSchema | | 

# SampleresourceIdSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
202 | [ApiResponseFor202](#update_sample_resource.ApiResponseFor202) | Successful response.
400 | [ApiResponseFor400](#update_sample_resource.ApiResponseFor400) | Parameter must be integer, payload must be of type SampleResource
404 | [ApiResponseFor404](#update_sample_resource.ApiResponseFor404) | Resource not found

#### update_sample_resource.ApiResponseFor202
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### update_sample_resource.ApiResponseFor400
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

#### update_sample_resource.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

No authorization required

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

