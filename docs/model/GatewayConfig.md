# GatewayConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**path_type** | **str** | Ingress path type  | 
**path** | **str** | Default target path prefix for applications endpoints. To use regular expressions (e.g.&#39;/(pattern)&#39;), also set &#x60;route_type&#x60; to  &#x60;ImplementationSpecific&#x60;.  | 

## Example

```python
from cloudharness_model.models.gateway_config import GatewayConfig

# TODO update the JSON string below
json = "{}"
# create an instance of GatewayConfig from a JSON string
gateway_config_instance = GatewayConfig.from_json(json)
# print the JSON string representation of the object
print(GatewayConfig.to_json())

# convert the object into a dict
gateway_config_dict = gateway_config_instance.to_dict()
# create an instance of GatewayConfig from a dict
gateway_config_from_dict = GatewayConfig.from_dict(gateway_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


