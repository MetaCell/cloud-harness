# cloudharness-cli.workflows
Workflows API

This Python package is automatically generated by the [OpenAPI Generator](https://openapi-generator.tech) project:

- API version: 0.1.0
- Package version: 1.0.0
- Build package: org.openapitools.codegen.languages.PythonClientCodegen

## Requirements.

Python 2.7 and 3.4+

## Installation & Usage
### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git
```
(you may need to run `pip` with root permission: `sudo pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git`)

Then import the package:
```python
import cloudharness_cli.workflows
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```
(or `sudo python setup.py install` to install the package for all users)

Then import the package:
```python
import cloudharness_cli.workflows
```

## Getting Started

Please follow the [installation procedure](#installation--usage) and then run the following:

```python
from __future__ import print_function
import time
import cloudharness_cli.workflows
from cloudharness_cli.workflows.rest import ApiException
from pprint import pprint


# Defining host is optional and default to https://workflows.cloudharness.metacell.us
configuration.host = "https://workflows.cloudharness.metacell.us"
# Enter a context with an instance of the API client
with cloudharness_cli.workflows.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.workflows.CreateAndAccessApi(api_client)
    name = 'name_example' # str | 

    try:
        # deletes operation by name
        api_instance.delete_operation(name)
    except ApiException as e:
        print("Exception when calling CreateAndAccessApi->delete_operation: %s\n" % e)
    
```

## Documentation for API Endpoints

All URIs are relative to *https://workflows.cloudharness.metacell.us*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*CreateAndAccessApi* | [**delete_operation**](docs/workflows/CreateAndAccessApi.md#delete_operation) | **DELETE** /operations/{name} | deletes operation by name
*CreateAndAccessApi* | [**get_operation**](docs/workflows/CreateAndAccessApi.md#get_operation) | **GET** /operations/{name} | get operation by name
*CreateAndAccessApi* | [**list_operations**](docs/workflows/CreateAndAccessApi.md#list_operations) | **GET** /operations | lists operations
*CreateAndAccessApi* | [**log_operation**](docs/workflows/CreateAndAccessApi.md#log_operation) | **GET** /operations/{name}/logs | get operation by name


## Documentation For Models

 - [Operation](docs/workflows/Operation.md)
 - [OperationSearchResult](docs/workflows/OperationSearchResult.md)
 - [OperationStatus](docs/workflows/OperationStatus.md)
 - [SearchResultData](docs/workflows/SearchResultData.md)


## Documentation For Authorization

 All endpoints do not require authorization.

## Author

cloudharness@metacell.us


# cloudharness-cli.common
Cloud Harness Platform - Reference CH service API

This Python package is automatically generated by the [OpenAPI Generator](https://openapi-generator.tech) project:

- API version: 0.1.0
- Package version: 1.0.0
- Build package: org.openapitools.codegen.languages.PythonClientCodegen

## Requirements.

Python 2.7 and 3.4+

## Installation & Usage
### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git
```
(you may need to run `pip` with root permission: `sudo pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git`)

Then import the package:
```python
import cloudharness_cli.common
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```
(or `sudo python setup.py install` to install the package for all users)

Then import the package:
```python
import cloudharness_cli.common
```

## Getting Started

Please follow the [installation procedure](#installation--usage) and then run the following:

```python
from __future__ import print_function
import time
import cloudharness_cli.common
from cloudharness_cli.common.rest import ApiException
from pprint import pprint


# Defining host is optional and default to http://localhost/api
configuration.host = "http://localhost/api"
# Enter a context with an instance of the API client
with cloudharness_cli.common.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.common.SentryApi(api_client)
    appname = 'appname_example' # str | 

    try:
        # Gets the Sentry DSN for a given application
        api_response = api_instance.getdsn(appname)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling SentryApi->getdsn: %s\n" % e)
    
```

## Documentation for API Endpoints

All URIs are relative to *http://localhost/api*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*SentryApi* | [**getdsn**](docs/common/SentryApi.md#getdsn) | **GET** /sentry/getdsn/{appname} | Gets the Sentry DSN for a given application


## Documentation For Models



## Documentation For Authorization

 All endpoints do not require authorization.

## Author




# cloudharness-cli.samples
CloudHarness Sample api

This Python package is automatically generated by the [OpenAPI Generator](https://openapi-generator.tech) project:

- API version: 0.1.0
- Package version: 1.0.0
- Build package: org.openapitools.codegen.languages.PythonClientCodegen

## Requirements.

Python 2.7 and 3.4+

## Installation & Usage
### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git
```
(you may need to run `pip` with root permission: `sudo pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git`)

Then import the package:
```python
import cloudharness_cli.samples
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```
(or `sudo python setup.py install` to install the package for all users)

Then import the package:
```python
import cloudharness_cli.samples
```

## Getting Started

Please follow the [installation procedure](#installation--usage) and then run the following:

```python
from __future__ import print_function
import time
import cloudharness_cli.samples
from cloudharness_cli.samples.rest import ApiException
from pprint import pprint

configuration = cloudharness_cli.samples.Configuration()
# Configure Bearer authorization (JWT): bearerAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to https://samples.cloudharness.metacell.us/api
configuration.host = "https://samples.cloudharness.metacell.us/api"

# Defining host is optional and default to https://samples.cloudharness.metacell.us/api
configuration.host = "https://samples.cloudharness.metacell.us/api"
# Enter a context with an instance of the API client
with cloudharness_cli.samples.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cloudharness_cli.samples.AuthApi(api_client)
    
    try:
        # Check if the token is valid. Get a token by logging into the base url
        api_response = api_instance.valid_token()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling AuthApi->valid_token: %s\n" % e)
    
```

## Documentation for API Endpoints

All URIs are relative to *https://samples.cloudharness.metacell.us/api*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*AuthApi* | [**valid_token**](docs/samples/AuthApi.md#valid_token) | **GET** /valid | Check if the token is valid. Get a token by logging into the base url
*WorkflowsApi* | [**error**](docs/samples/WorkflowsApi.md#error) | **GET** /error | test sentry is working
*WorkflowsApi* | [**submit_async**](docs/samples/WorkflowsApi.md#submit_async) | **GET** /operation_async | Send an asynchronous operation
*WorkflowsApi* | [**submit_sync**](docs/samples/WorkflowsApi.md#submit_sync) | **GET** /operation_sync | Send a synchronous operation
*WorkflowsApi* | [**submit_sync_with_results**](docs/samples/WorkflowsApi.md#submit_sync_with_results) | **GET** /operation_sync_results | Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud


## Documentation For Models

 - [InlineResponse202](docs/samples/InlineResponse202.md)
 - [InlineResponse202Task](docs/samples/InlineResponse202Task.md)
 - [Valid](docs/samples/Valid.md)


## Documentation For Authorization


## bearerAuth

- **Type**: Bearer authentication (JWT)


## Author

cloudharness@metacell.us


