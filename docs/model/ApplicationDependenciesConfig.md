# cloudharness_model.model.application_dependencies_config.ApplicationDependenciesConfig

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
dict, frozendict.frozendict,  | frozendict.frozendict,  |  | 

### Dictionary Keys
Key | Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | ------------- | -------------
**[hard](#hard)** | list, tuple,  | tuple,  | Hard dependencies indicate that the application may not start without these other applications. | [optional] 
**[soft](#soft)** | list, tuple,  | tuple,  | Soft dependencies indicate that the application will work partially without these other applications. | [optional] 
**[build](#build)** | list, tuple,  | tuple,  | Hard dependencies indicate that the application Docker image build requires these base/common images | [optional] 
**[git](#git)** | list, tuple,  | tuple,  |  | [optional] 
**any_string_name** | dict, frozendict.frozendict, str, date, datetime, int, float, bool, decimal.Decimal, None, list, tuple, bytes, io.FileIO, io.BufferedReader | frozendict.frozendict, str, BoolClass, decimal.Decimal, NoneClass, tuple, bytes, FileIO | any string name can be used but the value must be the correct type | [optional]

# hard

Hard dependencies indicate that the application may not start without these other applications.

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Hard dependencies indicate that the application may not start without these other applications. | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

# soft

Soft dependencies indicate that the application will work partially without these other applications.

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Soft dependencies indicate that the application will work partially without these other applications. | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

# build

Hard dependencies indicate that the application Docker image build requires these base/common images

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  | Hard dependencies indicate that the application Docker image build requires these base/common images | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
items | str,  | str,  |  | 

# git

## Model Type Info
Input Type | Accessed Type | Description | Notes
------------ | ------------- | ------------- | -------------
list, tuple,  | tuple,  |  | 

### Tuple Items
Class Name | Input Type | Accessed Type | Description | Notes
------------- | ------------- | ------------- | ------------- | -------------
[**GitDependencyConfig**](GitDependencyConfig.md) | [**GitDependencyConfig**](GitDependencyConfig.md) | [**GitDependencyConfig**](GitDependencyConfig.md) |  | 

[[Back to Model list]](../../README.md#documentation-for-models) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to README]](../../README.md)

