# GatewayGlobalConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | [optional] 
**name** | **str** |  | [optional] 
**path_type** | **str** | Ingress path type  | [optional] 
**path** | **str** | Default target path prefix for applications endpoints. To use regular expressions (e.g.&#39;/(pattern)&#39;), also set &#x60;route_type&#x60; to  &#x60;ImplementationSpecific&#x60;.  | [optional] 
**ssl_redirect** | **bool** |  | [optional] 
**tls** | [**GatewayGlobalConfigAllOfTls**](GatewayGlobalConfigAllOfTls.md) |  | [optional] 
**letsencrypt** | [**GatewayGlobalConfigAllOfLetsencrypt**](GatewayGlobalConfigAllOfLetsencrypt.md) |  | [optional] 
**enabled** | **bool** |  | [optional] 

## Example

```python
from cloudharness_model.models.gateway_global_config import GatewayGlobalConfig

# TODO update the JSON string below
json = "{}"
# create an instance of GatewayGlobalConfig from a JSON string
gateway_global_config_instance = GatewayGlobalConfig.from_json(json)
# print the JSON string representation of the object
print(GatewayGlobalConfig.to_json())

# convert the object into a dict
gateway_global_config_dict = gateway_global_config_instance.to_dict()
# create an instance of GatewayGlobalConfig from a dict
gateway_global_config_from_dict = GatewayGlobalConfig.from_dict(gateway_global_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


