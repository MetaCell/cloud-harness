# BackupConfig



## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**active** | **bool** |  | [optional] 
**keep_days** | **int** |  | [optional] 
**keep_weeks** | **int** |  | [optional] 
**keep_months** | **int** |  | [optional] 
**schedule** | **str** | Cron expression | [optional] 
**suffix** | **object** | The file suffix added to backup files | [optional] 
**volumesize** | **str** | The volume size for backups (all backups share the same volume) | [optional] 
**dir** | **str** |  | 
**resources** | [**DeploymentResourcesConf**](DeploymentResourcesConf.md) |  | 

## Example

```python
from cloudharness_model.models.backup_config import BackupConfig

# TODO update the JSON string below
json = "{}"
# create an instance of BackupConfig from a JSON string
backup_config_instance = BackupConfig.from_json(json)
# print the JSON string representation of the object
print(BackupConfig.to_json())

# convert the object into a dict
backup_config_dict = backup_config_instance.to_dict()
# create an instance of BackupConfig from a dict
backup_config_from_dict = BackupConfig.from_dict(backup_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


