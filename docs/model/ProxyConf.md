# ProxyConf



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**forwarded_headers** | **bool** |  | [optional] 
**payload** | [**ProxyPayloadConf**](ProxyPayloadConf.md) |  | [optional] 
**timeout** | [**ProxyTimeoutConf**](ProxyTimeoutConf.md) |  | [optional] 
**gatekeeper** | [**GatekeeperConf**](GatekeeperConf.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.proxy_conf import ProxyConf

# TODO update the JSON string below
json = "{}"
# create an instance of ProxyConf from a JSON string
proxy_conf_instance = ProxyConf.from_json(json)
# print the JSON string representation of the object
print(ProxyConf.to_json())

# convert the object into a dict
proxy_conf_dict = proxy_conf_instance.to_dict()
# create an instance of ProxyConf from a dict
proxy_conf_from_dict = ProxyConf.from_dict(proxy_conf_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


