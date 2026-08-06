# GatewayGlobalConfigAllOfLetsencrypt



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Whether to provision a cert-manager ACME Issuer for Let&#39;s Encrypt. Set to false to use externally provided TLS Secrets without ACME (e.g. ACM/ALB, commercial wildcards, internal CAs, air-gapped clusters).  | [optional] 
**email** | **str** |  | [optional] 
**private_key_secret_name** | **str** | Name of the Secret cert-manager uses to store the ACME account private key. Defaults to &#x60;tls-secret-issuer&#x60;.  | [optional] 
**solvers** | **List[Dict[str, object]]** | ACME solvers passed through to the cert-manager Issuer. Defaults to an http01 solver using the configured ingressClass. Set to a dns01 solver list to obtain certificates for non-public domains.  | [optional] 
**secrets** | **Dict[str, Dict[str, str]]** | Credential Secrets created in the namespace alongside the Issuer. Map of &#x60;&lt;secret-name&gt;&#x60; to a &#x60;&lt;key&gt;: &lt;value&gt;&#x60; map rendered as &#x60;stringData&#x60;. Reference these from &#x60;solvers&#x60;.  | [optional] 

## Example

```python
from cloudharness_model.models.gateway_global_config_all_of_letsencrypt import GatewayGlobalConfigAllOfLetsencrypt

# TODO update the JSON string below
json = "{}"
# create an instance of GatewayGlobalConfigAllOfLetsencrypt from a JSON string
gateway_global_config_all_of_letsencrypt_instance = GatewayGlobalConfigAllOfLetsencrypt.from_json(json)
# print the JSON string representation of the object
print(GatewayGlobalConfigAllOfLetsencrypt.to_json())

# convert the object into a dict
gateway_global_config_all_of_letsencrypt_dict = gateway_global_config_all_of_letsencrypt_instance.to_dict()
# create an instance of GatewayGlobalConfigAllOfLetsencrypt from a dict
gateway_global_config_all_of_letsencrypt_from_dict = GatewayGlobalConfigAllOfLetsencrypt.from_dict(gateway_global_config_all_of_letsencrypt_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


