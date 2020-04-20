# CloudHarness Applications

Here we put applications intended to run on the cluster.

Each application is intended as a http micro service running on the cluster.
An application installation is uniquely defined by a Docker file.

## Define a REST application with openapi
The preferred way to define an application is through the openapi specification. The code for the Python-flask service 
and the Python client
are automatically generated with the script `utilities/openapi-generate.py`

1. Add the application inside `applications/[APPLICATION_NAME]`
1. Add the openapi yaml specification inside `applications/[APPLICATION_NAME]/api/[APPLICATION_NAME].yaml`
1. Define openapi configuration `applications/[APPLICATION_NAME]/api/config.json`. The name of the package (say,
`PACKAGE_NAME`) can be configured here. By convention, the package name is `[APPLICATION_NAME]`
1. Run `python utilities/openapi-generate.py` to generate code stubs

After generating the codeChange the Dockerfile in order to inherit from the main Docker file:

```dockerfile
ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}
```

The only code that should be modified shall go inside `src/[PACKAGE_NAME]/controllers`.
After modifying the controllers, add the following line to `.openapi-generator-ignore`:

```
*/controllers/*
Dockerfile
```

## Define an application without openapi
1. Add the application inside `applications/[APPLICATION_NAME]` with a Docker file in it. The Docker file must inherit
from `r.cfcr.io/tarelli/cloudharness-base` in order to get access to cloudharness libraries.
1. Define values.yaml inside the file in order to specify custom values for the application


## Update deployment

See the [deployment section](../deployment/README.md)