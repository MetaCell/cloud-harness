# cloudharness_model.model.application_harness_config.ApplicationHarnessConfig

Define helm variables that allow CloudHarness to enable and configure your  application's deployment

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  | Define helm variables that allow CloudHarness to enable and configure your  application&#x27;s deployment | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**deployment** | [**DeploymentAutoArtifactConfig**](DeploymentAutoArtifactConfig.md) | [**DeploymentAutoArtifactConfig**](DeploymentAutoArtifactConfig.md) |  | [optional] 
**service** | [**ServiceAutoArtifactConfig**](ServiceAutoArtifactConfig.md) | [**ServiceAutoArtifactConfig**](ServiceAutoArtifactConfig.md) |  | [optional] 
**subdomain** | str,  | str,  | If specified, an ingress will be created at [subdomain].[.Values.domain] | [optional] 
**[aliases](#aliases)** | list, tuple,  | tuple,  | If specified, an ingress will be created at [alias].[.Values.domain] for each alias | [optional] 
**domain** | str,  | str,  | If specified, an ingress will be created at [domain] | [optional] 
**dependencies** | [**ApplicationDependenciesConfig**](ApplicationDependenciesConfig.md) | [**ApplicationDependenciesConfig**](ApplicationDependenciesConfig.md) |  | [optional] 
**secured** | bool,  | BoolClass,  | When true, the application is shielded with a getekeeper | [optional] 
**[uri_role_mapping](#uri_role_mapping)** | list, tuple,  | tuple,  | Map uri/roles to secure with the Gatekeeper (if &#x60;secured: true&#x60;) | [optional] 
**secrets** | [**SimpleMap**](SimpleMap.md) | [**SimpleMap**](SimpleMap.md) |  | [optional] 
**[use_services](#use_services)** | list, tuple,  | tuple,  | Specify which services this application uses in the frontend to create proxy ingresses. e.g.  &#x60;&#x60;&#x60; - name: samples &#x60;&#x60;&#x60; | [optional] 
**database** | [**DatabaseDeploymentConfig**](DatabaseDeploymentConfig.md) | [**DatabaseDeploymentConfig**](DatabaseDeploymentConfig.md) |  | [optional] 
**[resources](#resources)** | list, tuple,  | tuple,  | Application file resources. Maps from deploy/resources folder and mounts as configmaps | [optional] 
**readinessProbe** | [**ApplicationProbe**](ApplicationProbe.md) | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**startupProbe** | [**ApplicationProbe**](ApplicationProbe.md) | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**livenessProbe** | [**ApplicationProbe**](ApplicationProbe.md) | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**sourceRoot** | [**Filename**](Filename.md) | [**Filename**](Filename.md) |  | [optional] 
**name** | str,  | str,  | Application&#x27;s name. Do not edit, the value is automatically set from the application directory&#x27;s name | [optional] 
**jupyterhub** | [**JupyterHubConfig**](JupyterHubConfig.md) | [**JupyterHubConfig**](JupyterHubConfig.md) |  | [optional] 
**accounts** | [**ApplicationAccountsConfig**](ApplicationAccountsConfig.md) | [**ApplicationAccountsConfig**](ApplicationAccountsConfig.md) |  | [optional] 
**test** | [**ApplicationTestConfig**](ApplicationTestConfig.md) | [**ApplicationTestConfig**](ApplicationTestConfig.md) |  | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, bool, None, list, tuple, bytes, io.FileIO, io.BufferedReader,  | frozendict.frozendict, str, decimal.Decimal, BoolClass, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

# aliases

If specified, an ingress will be created at [alias].[.Values.domain] for each alias

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | If specified, an ingress will be created at [alias].[.Values.domain] for each alias | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

# uri_role_mapping

Map uri/roles to secure with the Gatekeeper (if `secured: true`)

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Map uri/roles to secure with the Gatekeeper (if &#x60;secured: true&#x60;) | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
[**UriRoleMappingConfig**](UriRoleMappingConfig.md) | [**UriRoleMappingConfig**](UriRoleMappingConfig.md) | [**UriRoleMappingConfig**](UriRoleMappingConfig.md) |  | 

# use_services

Specify which services this application uses in the frontend to create proxy ingresses. e.g.  ``` - name: samples ```

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Specify which services this application uses in the frontend to create proxy ingresses. e.g.  &#x60;&#x60;&#x60; - name: samples &#x60;&#x60;&#x60; | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

# resources

Application file resources. Maps from deploy/resources folder and mounts as configmaps

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Application file resources. Maps from deploy/resources folder and mounts as configmaps | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
[**FileResourcesConfig**](FileResourcesConfig.md) | [**FileResourcesConfig**](FileResourcesConfig.md) | [**FileResourcesConfig**](FileResourcesConfig.md) |  | 

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

