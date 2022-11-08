# cloudharness_cli.volumemanager.model.persistent_volume_claim.PersistentVolumeClaim

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**name** | str,  | str,  | Unique name for the Persisten Volume Claim | [optional] 
**namespace** | str,  | str,  | The namespace where the Persistent Volume Claim resides in | [optional] 
**accessmode** | str,  | str,  | The accessmode of the Persistent Volume Claim | [optional] 
**size** | str,  | str,  | The size of the Persistent Volume Claim. | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

