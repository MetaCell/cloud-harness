# ApplicationProbe

Define a Kubernetes probe See also the [official documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**path** | **str** |  | 
**period_seconds** | **float** |  | [optional] 
**failure_threshold** | **float** |  | [optional] 
**initial_delay_seconds** | **float** |  | [optional] 

## Example

```python
from cloudharness_model.models.application_probe import ApplicationProbe

# TODO update the JSON string below
json = "{}"
# create an instance of ApplicationProbe from a JSON string
application_probe_instance = ApplicationProbe.from_json(json)
# print the JSON string representation of the object
print ApplicationProbe.to_json()

# convert the object into a dict
application_probe_dict = application_probe_instance.to_dict()
# create an instance of ApplicationProbe from a dict
application_probe_form_dict = application_probe.from_dict(application_probe_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


