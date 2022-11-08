<a name="__pageTop"></a>
# cloudharness_cli.volumemanager.apis.tags.rest_api.RestApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**pvc_name_get**](#pvc_name_get) | **get** /pvc/{name} | Retrieve a Persistent Volume Claim from the Kubernetes repository.
[**pvc_post**](#pvc_post) | **post** /pvc | Create a Persistent Volume Claim in Kubernetes

# **pvc_name_get**
<a name="pvc_name_get"></a>
> PersistentVolumeClaim pvc_name_get(name)

Retrieve a Persistent Volume Claim from the Kubernetes repository.

### Example

* Bearer (JWT) Authentication (bearerAuth):
```python
import cloudharness_cli.volumemanager
from cloudharness_cli.volumemanager.apis.tags import rest_api
from cloudharness_cli/volumemanager.model.persistent_volume_claim import PersistentVolumeClaim
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.volumemanager.Configuration(
    host = "/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = cloudharness_cli.volumemanager.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)
# Enter a context with an instance of the API client
with cloudharness_cli.volumemanager.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = rest_api.RestApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'name': "name_example",
    }
    try:
        # Retrieve a Persistent Volume Claim from the Kubernetes repository.
        api_response = api_instance.pvc_name_get(
            path_params=path_params,
        )
        pprint(api_response)
    except cloudharness_cli.volumemanager.ApiException as e:
        print("Exception when calling RestApi->pvc_name_get: %s\n" % e)
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
200 | [ApiResponseFor200](#pvc_name_get.ApiResponseFor200) | The Persistent Volume Claim.
404 | [ApiResponseFor404](#pvc_name_get.ApiResponseFor404) | The Persistent Volume Claim was not found.

#### pvc_name_get.ApiResponseFor200
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor200ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor200ResponseBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**PersistentVolumeClaim**](../../models/PersistentVolumeClaim.md) |  | 


#### pvc_name_get.ApiResponseFor404
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

[bearerAuth](../../../README.md#bearerAuth)

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

# **pvc_post**
<a name="pvc_post"></a>
> PersistentVolumeClaim pvc_post(persistent_volume_claim_create)

Create a Persistent Volume Claim in Kubernetes

### Example

* Bearer (JWT) Authentication (bearerAuth):
```python
import cloudharness_cli.volumemanager
from cloudharness_cli.volumemanager.apis.tags import rest_api
from cloudharness_cli/volumemanager.model.persistent_volume_claim import PersistentVolumeClaim
from cloudharness_cli/volumemanager.model.persistent_volume_claim_create import PersistentVolumeClaimCreate
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.volumemanager.Configuration(
    host = "/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = cloudharness_cli.volumemanager.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)
# Enter a context with an instance of the API client
with cloudharness_cli.volumemanager.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = rest_api.RestApi(api_client)

    # example passing only required values which don't have defaults set
    body = PersistentVolumeClaimCreate(
        name="pvc-1",
        size="2Gi (see also https://github.com/kubernetes/community/blob/master/contributors/design-proposals/scheduling/resources.md#resource-quantities)",
    )
    try:
        # Create a Persistent Volume Claim in Kubernetes
        api_response = api_instance.pvc_post(
            body=body,
        )
        pprint(api_response)
    except cloudharness_cli.volumemanager.ApiException as e:
        print("Exception when calling RestApi->pvc_post: %s\n" % e)
```
### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
body | typing.Union[SchemaForRequestBodyApplicationJson] | required |
content_type | str | optional, default is 'application/json' | Selects the schema and serialization of the request body
accept_content_types | typing.Tuple[str] | default is ('application/json', ) | Tells the server the content type(s) that are accepted by the client
stream | bool | default is False | if True then the response.content will be streamed and loaded from a file like object. When downloading a file, set this to True to force the code to deserialize the content to a FileSchema file
timeout | typing.Optional[typing.Union[int, typing.Tuple]] | default is None | the timeout used by the rest client
skip_deserialization | bool | default is False | when True, headers and body will be unset and an instance of api_client.ApiResponseWithoutDeserialization will be returned

### body

# SchemaForRequestBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**PersistentVolumeClaimCreate**](../../models/PersistentVolumeClaimCreate.md) |  | 


### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
201 | [ApiResponseFor201](#pvc_post.ApiResponseFor201) | Save successful.
400 | [ApiResponseFor400](#pvc_post.ApiResponseFor400) | The Persistent Volume Claim already exists.

#### pvc_post.ApiResponseFor201
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | typing.Union[SchemaFor201ResponseBodyApplicationJson, ] |  |
headers | Unset | headers were not defined |

# SchemaFor201ResponseBodyApplicationJson
Type | Description  | Notes
------------- | ------------- | -------------
[**PersistentVolumeClaim**](../../models/PersistentVolumeClaim.md) |  | 


#### pvc_post.ApiResponseFor400
Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
response | urllib3.HTTPResponse | Raw response |
body | Unset | body was not defined |
headers | Unset | headers were not defined |

### Authorization

[bearerAuth](../../../README.md#bearerAuth)

[[Back to top]](#__pageTop) [[Back to API list]](../../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../../README.md#documentation-for-models) [[Back to README]](../../../README.md)

