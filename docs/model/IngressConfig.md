# IngressConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**auto** | **bool** | When true, enables automatic template | 
**name** | **str** |  | [optional] 
**ssl_redirect** | **bool** |  | [optional] 
**letsencrypt** | [**IngressConfigAllOfLetsencrypt**](IngressConfigAllOfLetsencrypt.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.ingress_config import IngressConfig

# TODO update the JSON string below
json = "{}"
# create an instance of IngressConfig from a JSON string
ingress_config_instance = IngressConfig.from_json(json)
# print the JSON string representation of the object
print IngressConfig.to_json()

# convert the object into a dict
ingress_config_dict = ingress_config_instance.to_dict()
# create an instance of IngressConfig from a dict
ingress_config_form_dict = ingress_config.from_dict(ingress_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


