# BackupS3Config

S3 credentials configuration for CNPG Barman backups

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**region** | **str** | AWS region | [optional] 
**access_key_id** | [**NameValue**](NameValue.md) |  | [optional] 
**secret_access_key** | [**NameValue**](NameValue.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.backup_s3_config import BackupS3Config

# TODO update the JSON string below
json = "{}"
# create an instance of BackupS3Config from a JSON string
backup_s3_config_instance = BackupS3Config.from_json(json)
# print the JSON string representation of the object
print(BackupS3Config.to_json())

# convert the object into a dict
backup_s3_config_dict = backup_s3_config_instance.to_dict()
# create an instance of BackupS3Config from a dict
backup_s3_config_from_dict = BackupS3Config.from_dict(backup_s3_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


