# ProxyTimeoutConf



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**keepalive** | **int** |  | [optional] 
**read** | **int** |  | [optional] 
**send** | **int** |  | [optional] 

## Example

```python
from cloudharness_model.models.proxy_timeout_conf import ProxyTimeoutConf

# TODO update the JSON string below
json = "{}"
# create an instance of ProxyTimeoutConf from a JSON string
proxy_timeout_conf_instance = ProxyTimeoutConf.from_json(json)
# print the JSON string representation of the object
print(ProxyTimeoutConf.to_json())

# convert the object into a dict
proxy_timeout_conf_dict = proxy_timeout_conf_instance.to_dict()
# create an instance of ProxyTimeoutConf from a dict
proxy_timeout_conf_from_dict = ProxyTimeoutConf.from_dict(proxy_timeout_conf_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


