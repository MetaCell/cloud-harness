# GatekeeperConf



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**image** | **str** |  | [optional] 
**replicas** | **int** |  | [optional] 

## Example

```python
from cloudharness_model.models.gatekeeper_conf import GatekeeperConf

# TODO update the JSON string below
json = "{}"
# create an instance of GatekeeperConf from a JSON string
gatekeeper_conf_instance = GatekeeperConf.from_json(json)
# print the JSON string representation of the object
print(GatekeeperConf.to_json())

# convert the object into a dict
gatekeeper_conf_dict = gatekeeper_conf_instance.to_dict()
# create an instance of GatekeeperConf from a dict
gatekeeper_conf_from_dict = GatekeeperConf.from_dict(gatekeeper_conf_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


