# ApplicationHarnessConfig

Define helm variables that allow CloudHarness to enable and configure your  application's deployment

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**deployment** | [**DeploymentAutoArtifactConfig**](DeploymentAutoArtifactConfig.md) |  | [optional] 
**service** | [**ServiceAutoArtifactConfig**](ServiceAutoArtifactConfig.md) |  | [optional] 
**subdomain** | **str** | If specified, an ingress will be created at [subdomain].[.Values.domain] | [optional] 
**aliases** | **List[str]** | If specified, an ingress will be created at [alias].[.Values.domain] for each alias | [optional] 
**domain** | **str** | If specified, an ingress will be created at [domain] | [optional] 
**dependencies** | [**ApplicationDependenciesConfig**](ApplicationDependenciesConfig.md) |  | [optional] 
**secured** | **bool** | When true, the application is shielded with a getekeeper | [optional] 
**uri_role_mapping** | [**List[UriRoleMappingConfig]**](UriRoleMappingConfig.md) | Map uri/roles to secure with the Gatekeeper (if &#x60;secured: true&#x60;) | [optional] 
**secrets** | **Dict[str, str]** |  | [optional] 
**use_services** | **List[str]** | Specify which services this application uses in the frontend to create proxy ingresses. e.g.  &#x60;&#x60;&#x60; - name: samples &#x60;&#x60;&#x60; | [optional] 
**database** | [**DatabaseDeploymentConfig**](DatabaseDeploymentConfig.md) |  | [optional] 
**resources** | [**List[FileResourcesConfig]**](FileResourcesConfig.md) | Application file resources. Maps from deploy/resources folder and mounts as configmaps | [optional] 
**readiness_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**startup_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**liveness_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**source_root** | **str** |  | [optional] 
**name** | **str** | Application&#39;s name. Do not edit, the value is automatically set from the application directory&#39;s name | [optional] 
**jupyterhub** | [**JupyterHubConfig**](JupyterHubConfig.md) |  | [optional] 
**accounts** | [**ApplicationAccountsConfig**](ApplicationAccountsConfig.md) |  | [optional] 
**test** | [**ApplicationTestConfig**](ApplicationTestConfig.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.application_harness_config import ApplicationHarnessConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ApplicationHarnessConfig from a JSON string
application_harness_config_instance = ApplicationHarnessConfig.from_json(json)
# print the JSON string representation of the object
print(ApplicationHarnessConfig.to_json())

# convert the object into a dict
application_harness_config_dict = application_harness_config_instance.to_dict()
# create an instance of ApplicationHarnessConfig from a dict
application_harness_config_from_dict = ApplicationHarnessConfig.from_dict(application_harness_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


