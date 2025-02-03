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
import cloudharness_cli.volumemanager
from cloudharness_cli.volumemanager.models.persistent_volume_claim import PersistentVolumeClaim
from cloudharness_cli.volumemanager.rest import ApiException
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
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with cloudharness_cli.volumemanager.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.volumemanager.RestApi(api_client)
    name = 'name_example' # str | The name of the Persistent Volume Claim to be retrieved

    try:
        # Retrieve a Persistent Volume Claim from the Kubernetes repository.
        api_response = api_instance.pvc_name_get(name)
        print("The response of RestApi->pvc_name_get:\n")
        pprint(api_response)
    except Exception as e:
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
import cloudharness_cli.volumemanager
from cloudharness_cli.volumemanager.models.persistent_volume_claim import PersistentVolumeClaim
from cloudharness_cli.volumemanager.models.persistent_volume_claim_create import PersistentVolumeClaimCreate
from cloudharness_cli.volumemanager.rest import ApiException
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
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with cloudharness_cli.volumemanager.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.volumemanager.RestApi(api_client)
    persistent_volume_claim_create = cloudharness_cli.volumemanager.PersistentVolumeClaimCreate() # PersistentVolumeClaimCreate | The Persistent Volume Claim to create.

    try:
        # Create a Persistent Volume Claim in Kubernetes
        api_response = api_instance.pvc_post(persistent_volume_claim_create)
        print("The response of RestApi->pvc_post:\n")
        pprint(api_response)
    except Exception as e:
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

