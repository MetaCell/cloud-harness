# BackupOffloadConfig

Configuration for CNPG Barman object store backup offloading

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**retention_policy** | **str** | Retention policy for CNPG Barman backups (e.g. 30d) | [optional] 
**destination_path** | **str** | Barman object store destination (e.g. s3://bucket/path or gs://bucket/path) | [optional] 
**endpoint_url** | **str** | Endpoint URL override for S3-compatible stores (e.g. MinIO) | [optional] 
**s3** | [**BackupS3Config**](BackupS3Config.md) |  | [optional] 
**gcs** | [**BackupGcsConfig**](BackupGcsConfig.md) |  | [optional] 

## Example

```python
from cloudharness_model.models.backup_offload_config import BackupOffloadConfig

# TODO update the JSON string below
json = "{}"
# create an instance of BackupOffloadConfig from a JSON string
backup_offload_config_instance = BackupOffloadConfig.from_json(json)
# print the JSON string representation of the object
print(BackupOffloadConfig.to_json())

# convert the object into a dict
backup_offload_config_dict = backup_offload_config_instance.to_dict()
# create an instance of BackupOffloadConfig from a dict
backup_offload_config_from_dict = BackupOffloadConfig.from_dict(backup_offload_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


