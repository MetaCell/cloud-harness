# BackupConfig


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dir** | [**Filename**](Filename.md) |  | 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | 
**active** | **bool** |  | [optional] 
**keep_days** | **int** |  | [optional] 
**keep_weeks** | **int** |  | [optional] 
**keep_months** | **int** |  | [optional] 
**schedule** | **str** | Cron expression | [optional] 
**suffix** | **bool, date, datetime, dict, float, int, list, str, none_type** | The file suffix added to backup files | [optional] 
**volumesize** | **str** | The volume size for backups (all backups share the same volume) | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


