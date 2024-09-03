# Develop in the backend with CloudHarness

## Create a default Backend with Flask and Openapi

Although there is no restriction on the technology used to build
your application, starting from a semi auto-generated Python/Flask application is the
recommended way to create a backend microservice within a 
CloudHarness based solution.

To create the initial scaffolding, run:

```
harness-application app-name
```

The development then can go through the following steps:
1. Edit the openapi file at `applications/app-name/api/openapi.yaml`. Can edit the yaml file directly or use more friendly interfaces like Apicurio Studio or SwaggerHub. It is recommended to use a different tag for every resource type: one controller is generated for each tag.
1. Regenerate the application code stubs with `harness-generate . -i`
1. *(optional)* edit the setup.py and requirements.txt according to your library requirements
1. Implement your logic inside `backend/app_name/controllers`. It is recommended to implement the actual application logic on custom files implementing the business logic and the service logic.
1. *(optional)*  add **/controllers to the .openapi-generator-ignore so that the controllers won't be overwritten by the next generation
1. *(optional)* customize the Dockerfile
1. *(optional)* add other custom endpoints

The application entry point is `backend/__main__.py`: it can be run as
a simple Python script or module to debug locally.


### Base libraries and images

The simplest way to use the shared CloudHarness functionality in an 
application is to inherit your application Docker image from one
of the base images.
The base images include preinstalled the CloufHarness common libraries.

Since the images are built together with the rest of the system,
we use arguments for the reference, like:

```dockerfile
ARG $CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE
...
```

For the image dependency to be recognized by the build scripts,
the dependencty must be declared in the `values.yaml` file of your application, e.g.:

```yaml
harness:
  dependencies:
    build:
    - cloudharness-base
```

Every image defined as a base image or a common image can be used as a
build dependency.

For more details about how to define your custom image and the available images, see [here](../../base-common-images.md).

For more info about dependencies, see [here](../dependencies.md)

## Use the CloudHarness runtime Python library

The CloudHarness runtime library shares some common functionality that
helps the backend development in Python.
The runtime library depends on the `cloudharness_models` library, which builds the common 
ground to understand and use the relevant data types.

The main functionality provided is:
- Access to the solution configuration and secrets
- Access and manipulate users, authentication and authorization
- Create and listen to orchestration events
- Create and monitor workflow operations

### Get applications references and configurations

The applications configuration api gives access to a proxy object
containing all the data from the values.yaml file at runtime.

The object returned is of type `cloudharness.applications.ApplicationConfiguration`,
a subtype of the wrapper [ApplicationConfig](../../model/ApplicationConfig.md).

```python
from cloudharness import applications

uut: applications.ApplicationConfiguration = applications.get_configuration('app1')

uut.is_auto_service() # has a service?
uut.is_auto_deployment() # has a deployment?
uut.is_sentry_enabled() # is sentry enabled?
uut.image_name # get the image name
uut.get_public_address() # get the public (external) address, as configured in Ingress
uut.get_service_address() # internal address to make calls to this application
```

### Check authentication and Authorization

See [accounts specific documentation](../../accounts.md#Backend-development).

### Run workflows

See the [workflows api](./workflows-api.md) dedicated document.

### Events and orchestration 

## Debug inside the cluster

See [here](../../build-deploy/local-deploy/debug.md).