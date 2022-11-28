# cloudharness_model.model.backup_config.BackupConfig

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | 
**dir** | [**Filename**](Filename.md) | [**Filename**](Filename.md) |  | 
**active** | bool,  | BoolClass,  |  | [optional] 
**keep_days** | decimal.Decimal, int,  | decimal.Decimal,  |  | [optional] 
**keep_weeks** | decimal.Decimal, int,  | decimal.Decimal,  |  | [optional] 
**keep_months** | decimal.Decimal, int,  | decimal.Decimal,  |  | [optional] 
**schedule** | str,  | str,  | Cron expression | [optional] 
**suffix** | dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, bool, None, list, tuple, bytes, io.FileIO, io.BufferedReader,  | frozendict.frozendict, str, decimal.Decimal, BoolClass, NoneClass, tuple, bytes, FileIO | The file suffix added to backup files | [optional] 
**volumesize** | str,  | str,  | The volume size for backups (all backups share the same volume) | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

