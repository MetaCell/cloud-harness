# ApplicationHarnessConfig


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**deployment** | [**DeploymentAutoArtifactConfig**](DeploymentAutoArtifactConfig.md) |  | [optional] 
**service** | [**ServiceAutoArtifactConfig**](ServiceAutoArtifactConfig.md) |  | [optional] 
**subdomain** | **str** | If specified, an ingress will be created at [subdomain].[.Values.domain] | [optional] 
**aliases** | **[str]** | If specified, an ingress will be created at [alias].[.Values.domain] for each alias | [optional] 
**domain** | **str** | If specified, an ingress will be created at [domain] | [optional] 
**dependencies** | [**ApplicationDependenciesConfig**](ApplicationDependenciesConfig.md) |  | [optional] 
**secured** | **bool** | When true, the application is shielded with a getekeeper | [optional] 
**uri_role_mapping** | [**[UriRoleMappingConfig]**](UriRoleMappingConfig.md) | Map uri/roles to secure with the Gatekeeper (if &#x60;secured: true&#x60;) | [optional] 
**secrets** | [**SimpleMap**](SimpleMap.md) |  | [optional] 
**use_services** | **[str]** | Specify which services this application uses in the frontend to create proxy ingresses. e.g.  &#x60;&#x60;&#x60; - name: samples &#x60;&#x60;&#x60; | [optional] 
**database** | [**DatabaseDeploymentConfig**](DatabaseDeploymentConfig.md) |  | [optional] 
**resources** | [**[FileResourcesConfig]**](FileResourcesConfig.md) | Application file resources. Maps from deploy/resources folder and mounts as configmaps | [optional] 
**readiness_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**startup_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**liveness_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**source_root** | [**Filename**](Filename.md) |  | [optional] 
**name** | **str** |  | [optional] 
**jupyterhub** | [**JupyterHubConfig**](JupyterHubConfig.md) |  | [optional] 
**accounts** | [**ApplicationAccountsConfig**](ApplicationAccountsConfig.md) |  | [optional] 
**test** | [**ApplicationTestConfig**](ApplicationTestConfig.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


