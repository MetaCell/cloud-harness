# HarnessMainConfig


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**local** | **bool** | If set to true, local DNS mapping is added to pods. | 
**secured_gatekeepers** | **bool** | Enables/disables Gatekeepers on secured applications. Set to false for testing/development | 
**domain** | **str** | The root domain | 
**namespace** | **str** | The K8s namespace. | 
**mainapp** | **str** | Defines the app to map to the root domain | 
**apps** | [**ApplicationsConfigsMap**](ApplicationsConfigsMap.md) |  | 
**registry** | [**RegistryConfig**](RegistryConfig.md) |  | [optional] 
**tag** | **str** | Docker tag used to push/pull the built images. | [optional] 
**env** | [**[NameValue]**](NameValue.md) | Environmental variables added to all pods | [optional] 
**privenv** | [**NameValue**](NameValue.md) |  | [optional] 
**backup** | [**BackupConfig**](BackupConfig.md) |  | [optional] 
**name** | **str** | Base name | [optional] 
**task_images** | [**SimpleMap**](SimpleMap.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


