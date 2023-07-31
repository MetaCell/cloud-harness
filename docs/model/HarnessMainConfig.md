# cloudharness_model.model.harness_main_config.HarnessMainConfig

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**mainapp** | str,  | str,  | Defines the app to map to the root domain | 
**domain** | str,  | str,  | The root domain | 
**namespace** | str,  | str,  | The K8s namespace. | 
**secured_gatekeepers** | bool,  | BoolClass,  | Enables/disables Gatekeepers on secured applications. Set to false for testing/development | 
**local** | bool,  | BoolClass,  | If set to true, local DNS mapping is added to pods. | 
**apps** | [**ApplicationsConfigsMap**](ApplicationsConfigsMap.md) | [**ApplicationsConfigsMap**](ApplicationsConfigsMap.md) |  | 
**registry** | [**RegistryConfig**](RegistryConfig.md) | [**RegistryConfig**](RegistryConfig.md) |  | [optional] 
**tag** | str,  | str,  | Docker tag used to push/pull the built images. | [optional] 
**[env](#env)** | list, tuple,  | tuple,  | Environmental variables added to all pods | [optional] 
**privenv** | [**NameValue**](NameValue.md) | [**NameValue**](NameValue.md) |  | [optional] 
**backup** | [**BackupConfig**](BackupConfig.md) | [**BackupConfig**](BackupConfig.md) |  | [optional] 
**name** | str,  | str,  | Base name | [optional] 
**task-images** | [**SimpleMap**](SimpleMap.md) | [**SimpleMap**](SimpleMap.md) |  | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

# env

Environmental variables added to all pods

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Environmental variables added to all pods | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
[**NameValue**](NameValue.md) | [**NameValue**](NameValue.md) | [**NameValue**](NameValue.md) |  | 

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

