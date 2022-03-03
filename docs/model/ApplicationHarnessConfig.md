# ApplicationHarnessConfig


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**deployment** | **bool, date, datetime, dict, float, int, list, str, none_type** | Defines reference deployment parameters. Values maps to k8s spec | [optional] 
**service** | **bool, date, datetime, dict, float, int, list, str, none_type** | Defines automatic service parameters. | [optional] 
**subdomain** | **str** | If specified, an ingress will be created at [subdomain].[.Values.domain] | [optional] 
**aliases** | **[str]** | If specified, an ingress will be created at [alias].[.Values.domain] for each alias | [optional] 
**domain** | **str** | If specified, an ingress will be created at [domain] | [optional] 
**dependencies** | **bool, date, datetime, dict, float, int, list, str, none_type** | Application dependencies are used to define what is required in the deployment when --include (-i) is used. Specify application names in the list. | [optional] 
**secured** | **bool** | When true, the application is shielded with a getekeeper | [optional] 
**uri_role_mapping** | [**[UriRoleMappingConfig]**](UriRoleMappingConfig.md) | Map uri/roles to secure with the Gatekeeper (if &#x60;secured: true&#x60;) | [optional] 
**secrets** | **bool, date, datetime, dict, float, int, list, str, none_type** | Define secrets will be mounted in the deployment  Define as  &#x60;&#x60;&#x60;yaml secrets:     secret_name: &#39;value&#39;  &#x60;&#x60;&#x60;  Values if left empty are randomly generated | [optional] 
**use_services** | **[str]** | Specify which services this application uses in the frontend to create proxy ingresses. e.g.  &#x60;&#x60;&#x60; - name: samples &#x60;&#x60;&#x60; | [optional] 
**database** | **bool, date, datetime, dict, float, int, list, str, none_type** |  | [optional] 
**resources** | [**[FileResourcesConfig]**](FileResourcesConfig.md) | Application file resources. Maps from deploy/resources folder and mounts as configmaps | [optional] 
**readiness_probe** | **bool, date, datetime, dict, float, int, list, str, none_type** |  | [optional] 
**startup_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**liveness_probe** | [**ApplicationProbe**](ApplicationProbe.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


