# cloudharness_cli.volumemanager.RestApi

All URIs are relative to */api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**pvc_name_get**](RestApi.md#pvc_name_get) | **GET** /pvc/{name} | Retrieve a Persistent Volume Claim from the Kubernetes repository.
[**pvc_post**](RestApi.md#pvc_post) | **POST** /pvc | Create a Persistent Volume Claim in Kubernetes


# **pvc_name_get**
> PersistentVolumeClaim pvc_name_get(name)

Retrieve a Persistent Volume Claim from the Kubernetes repository.

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import time
import cloudharness_cli.volumemanager
from cloudharness_cli.volumemanager.api import rest_api
from cloudharness_cli.volumemanager.model.persistent_volume_claim import PersistentVolumeClaim
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
    name = "name_example" # str | The name of the Persistent Volume Claim to be retrieved

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a Persistent Volume Claim from the Kubernetes repository.
        api_response = api_instance.pvc_name_get(name)
        pprint(api_response)
    except cloudharness_cli.volumemanager.ApiException as e:
        print("Exception when calling RestApi->pvc_name_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| The name of the Persistent Volume Claim to be retrieved |

### Return type

[**PersistentVolumeClaim**](PersistentVolumeClaim.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | The Persistent Volume Claim. |  -  |
**404** | The Persistent Volume Claim was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **pvc_post**
> PersistentVolumeClaim pvc_post(persistent_volume_claim_create)

Create a Persistent Volume Claim in Kubernetes

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import time
import cloudharness_cli.volumemanager
from cloudharness_cli.volumemanager.api import rest_api
from cloudharness_cli.volumemanager.model.persistent_volume_claim_create import PersistentVolumeClaimCreate
from cloudharness_cli.volumemanager.model.persistent_volume_claim import PersistentVolumeClaim
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
    persistent_volume_claim_create = PersistentVolumeClaimCreate(
        name="pvc-1",
        size="2Gi (see also https://github.com/kubernetes/community/blob/master/contributors/design-proposals/scheduling/resources.md#resource-quantities)",
    ) # PersistentVolumeClaimCreate | The Persistent Volume Claim to create.

    # example passing only required values which don't have defaults set
    try:
        # Create a Persistent Volume Claim in Kubernetes
        api_response = api_instance.pvc_post(persistent_volume_claim_create)
        pprint(api_response)
    except cloudharness_cli.volumemanager.ApiException as e:
        print("Exception when calling RestApi->pvc_post: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **persistent_volume_claim_create** | [**PersistentVolumeClaimCreate**](PersistentVolumeClaimCreate.md)| The Persistent Volume Claim to create. |

### Return type

[**PersistentVolumeClaim**](PersistentVolumeClaim.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Save successful. |  -  |
**400** | The Persistent Volume Claim already exists. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

