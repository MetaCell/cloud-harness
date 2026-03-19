# BackupGcsConfig

GCS credentials configuration for CNPG Barman backups

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**application_credentials** | [**NameValue**](NameValue.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.backup_gcs_config import BackupGcsConfig

# TODO update the JSON string below
json = "{}"
# create an instance of BackupGcsConfig from a JSON string
backup_gcs_config_instance = BackupGcsConfig.from_json(json)
# print the JSON string representation of the object
print(BackupGcsConfig.to_json())

# convert the object into a dict
backup_gcs_config_dict = backup_gcs_config_instance.to_dict()
# create an instance of BackupGcsConfig from a dict
backup_gcs_config_from_dict = BackupGcsConfig.from_dict(backup_gcs_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


