<a name="__pageTop"></a>
# cloudharness_cli.common.apis.tags.sentry_api.SentryApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getdsn**](#getdsn) | **get** /sentry/getdsn/{appname} | Gets the Sentry DSN for a given application

# **getdsn**
<a name="getdsn"></a>
> str getdsn(appname)

Gets the Sentry DSN for a given application

Gets the Sentry DSN for a given application

### Example

```python
import cloudharness_cli.common
from cloudharness_cli.common.apis.tags import sentry_api
from pprint import pprint
# Defining the host is optional and defaults to /api
# See configuration.py for a list of all supported configuration parameters.
configuration = cloudharness_cli.common.Configuration(
    host = "/api"
)

# Enter a context with an instance of the API client
with cloudharness_cli.common.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = sentry_api.SentryApi(api_client)

    # example passing only required values which don't have defaults set
    path_params = {
        'appname': "appname_example",
    }
    try:
        # Gets the Sentry DSN for a given application
        api_response = api_instance.getdsn(
            path_params=path_params,
        )
        pprint(api_response)
    except cloudharness_cli.common.ApiException as e:
        print("Exception when calling SentryApi->getdsn: %s\n" % e)
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
appname | AppnameSchema | | 

# AppnameSchema

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
str,  | str,  |  | 

### Return Types, Responses

Code | Class | Description
------------- | ------------- | -------------
n/a | api_client.ApiResponseWithoutDeserialization | When skip_deserialization is True this response is returned
200 | [ApiResponseFor200](#getdsn.ApiResponseFor200) | Sentry DSN for the given application

#### getdsn.ApiResponseFor200
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

