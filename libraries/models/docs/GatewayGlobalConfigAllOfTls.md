# GatewayGlobalConfigAllOfTls

BYO TLS certificate configuration. Used when `letsencrypt.enabled` is false or `local` is true. Per-app entries override the file-based shared cert at `resources/certs/tls.crt|key`. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**certs** | [**Dict[str, GatewayGlobalConfigAllOfTlsCerts]**](GatewayGlobalConfigAllOfTlsCerts.md) | Map of &#x60;&lt;appName&gt;&#x60; to &#x60;{crt, key}&#x60; PEM strings. Materializes one &#x60;tls-secret-&lt;appName&gt;&#x60; Secret per entry of type &#x60;kubernetes.io/tls&#x60;.  | [optional] 

## Example

```python
from cloudharness_model.models.gateway_global_config_all_of_tls import GatewayGlobalConfigAllOfTls

# TODO update the JSON string below
json = "{}"
# create an instance of GatewayGlobalConfigAllOfTls from a JSON string
gateway_global_config_all_of_tls_instance = GatewayGlobalConfigAllOfTls.from_json(json)
# print the JSON string representation of the object
print(GatewayGlobalConfigAllOfTls.to_json())

# convert the object into a dict
gateway_global_config_all_of_tls_dict = gateway_global_config_all_of_tls_instance.to_dict()
# create an instance of GatewayGlobalConfigAllOfTls from a dict
gateway_global_config_all_of_tls_from_dict = GatewayGlobalConfigAllOfTls.from_dict(gateway_global_config_all_of_tls_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


