# Create a new applicaton

Any Dockerfile added in a subfolder below the [applications](../../applications) directory is interpreted as an application part of the deployment.

## Use harness-application

The `harness-application` cli tool creates new applications from predefinite code templates.
To create a new Flask base microservice application, run:

```bash
harness-application myapp
```

Other examples:

Create a web application
```bash
harness-application myapp -t webapp
```

Create a web application with Mongo database
```bash
harness-application myapp -t webapp -t db-mongo
```

For more info, `harness-application --help`

## Manual application creation

1. Add the application inside `applications/[APPLICATION_NAME]` with a Dockerfile in it
1. Define *deploy/values.yaml* inside the file in order to specify custom values for the application
1. (optional) Define specific helm template variables on *deploy/values.yaml*
1. (optional) Define the helm templates for the application inside `deploy/templates` (if any). In the helm template, it is recommended to use the automatically generated values from the `values.yaml`. The path of the variables will be .Values.myapp.myvariable
1. Run `harness-deployment`

### Use Openapi to generate REST microservices and web applications
The preferred way to define an application is through the openapi specification. The code for the Python-flask service 
and the Python client
are automatically generated with the script `harness-generate`

1. Add the application inside `applications/[APPLICATION_NAME]`
1. Add the openapi yaml specification inside `applications/[APPLICATION_NAME]/api/[APPLICATION_NAME].yaml`
1. Define openapi configuration `applications/[APPLICATION_NAME]/api/config.json`. The name of the package (say,
`PACKAGE_NAME`) can be configured here. By convention, the package name is `[APPLICATION_NAME]`
1. Run `harness-generate .` to generate code stubs

The only code that should be modified shall go inside `src/[PACKAGE_NAME]/controllers`.
After modifying the controllers, add the following line to `.openapi-generator-ignore`:

```
*/controllers/*
Dockerfile
```

## Define an application without openapi
1. Add the application inside `applications/[APPLICATION_NAME]` with a Docker file in it. The Docker file must inherit
from `cloudharness-base` in order to get access to cloudharness libraries.
1. Define values.yaml inside the file in order to specify custom values for the application


## From existing external image

To use an external image using the default deployment generator from Cloudharness, define the image inside `applications/my-external-app/deploy/values.yaml` file.
```
harness:
  deployment:
    auto: true
    image: nginx:1.0.0
```

To customize the helm templates to use, put them inside the *deploy* subdirectory.

## Application instances

An application can be deployed several times over, each deployment on its own subdomain and with
its own configuration and database. Each of those deployments is an *instance*, declared as a
directory under the application's `deploy/instances`:

```
applications/samples/
  Dockerfile
  deploy/
    values.yaml                # the application's configuration
    resources/
      example.yaml
      myConfig.json
    instances/
      instance1/               # the instance's name is its directory's
        values.yaml            # what this instance changes
        resources/
          example.yaml         # overrides the application's resource of the same name
        templates/             # optional, overlaid on the application's templates
```

The instance above is deployed as the application `samples-instance1`: that key names its service,
deployment, database, volume, gatekeeper and configmaps, and is how it is referenced on the command
line. It runs the image built for `samples` — an instance adds no build, so declare no Dockerfile
in it. The key must not take over one of the application's task images: an instance named `print`
on an application with a `tasks/print-file` is rejected, as `samples-print` would own
`samples-print-file`.

Everything else is inherited from the application, so an instance's `values.yaml` only carries what
it changes:

```yaml
harness:
  subdomain: samples1
  deployment:
    replicas: 1
```

Values are merged over the application's the usual way: mappings key by key, lists as a whole. An
instance overriding `uri_role_mapping` therefore replaces the whole list rather than adding to it.
Resources and templates are overlaid file by file, so an instance inherits every file it does not
override — above, `myConfig.json` comes from the application and `example.yaml` from the instance.

Environment specific values apply at both levels, the instance's taking precedence over the
application's:

```
deploy/instances/instance1/values-[ENV].yaml   # wins
deploy/instances/instance1/values.yaml
deploy/values-[ENV].yaml
deploy/values.yaml                             # loses
```

What identifies the application is never inherited, so that an instance never claims the
application's hosts or resources:

- `subdomain`, `aliases` and `domain`. An instance without a `subdomain` of its own answers on
  its directory's name, so `instances/samples1/` alone is served at `samples1.[DOMAIN]`; declare
  `subdomain: null` to give an instance no ingress at all
- the names of the service, deployment and database, which are derived from the instance key
- `deployment.volume.name`, prefixed with the instance key, so the instance never mounts the
  application's storage
- `database.connect_string`, emptied: an instance of an application using an externally managed
  database needs a connection string of its own. Set `database.auto: true` to have CloudHarness
  deploy a database of its own for it instead.

Instances are deployed together with their application: `harness-deployment -i samples` deploys
`samples` and all its instances, and `-e samples-instance1` leaves one out. CI builds and tests the
application only, since an instance runs the same image.

## Dependency to an existing Helm chart

TBD

## Dependency to a custom Helm chart

TDB

# Harness values and automatic templates

Cloud-harness creates a series of artifacts and configurations for each application, depending
on the values defined on the `deploy/values.yaml` file inside the application

Given an application on `applications/myapp`, the values file is located at `applications/myapp/deploy/values.yaml`.

The most important configuration entries are the following:

- `harness`: root of all auto templates configurations
  - `subdomain`: creates an entry to ingress on [subdomain].[Values.domain]
  - `domain`: creates an entry to ingress on [domain]
  - `secured`: if set to true, shields the access to the application requiring login
  - `uri_role_mapping` (`{uri, roles}[]`): if secured is true, used to map application urls to authenticated required roles
  - `deployment`: creates a deployment — see [Auto Deployments](./deployment.md)
    - `auto`: if true, creates the deployment automatically
    - `replicas`: number of pod replicas
    - `image`: pre-built image (leave blank to build from Dockerfile)
    - `port`: container port
    - `command` / `args`: override container entrypoint and arguments
    - `resources`: CPU and memory requests/limits
    - `volume`: persistent volume — see [Volumes](./volumes.md)
    - `network`: network policy — see [Network Policies](../network-policies.md)
    - `extraContainers`: init containers and sidecars — see [Auto Deployments § Extra containers](./deployment.md#extra-containers)
  - `livenessProbe` / `readinessProbe` / `startupProbe`: HTTP health probes — see [Auto Deployments § Health probes](./deployment.md#health-probes)
  - `service`:
    - `auto`: if true, creates the service automatically
  - `dependencies`: lists of applications/images this application depends from
    - `hard`: hard dependencies mean that they are required for this application to work properly
    - `soft`: the application will function for most of its functionality without this dependency
    - `build`: the images declared as build dependencies can be referred as dependency in the Dockerfile 
    - `git`: specify repos to be cloned before the container build
  - `database`: automatically generates a preconfigured database deployment for this application
    - `auto`: if true, turns on the database deployment functionality
    - `type`: one from `postgres` (default), `mongo`, `neo4j`
    - `postgres`: postgres specific configurations
    - `mongo`: mongo specific configurations
    - `neo4j`: neo4j specific configurations
  - `envmap`: add custom environment variables
    - `<environment_variable_name>`: `<environment_variable_value>`
    - ...
  - `env` (`{name, value}[]`): add custom environment variables (deprecated, please use `envmap`)
  - `resources`: mount files from  
  - `use_services` (`{name, src, dst}[]`): create reverse proxy endpoints in the ingress for the listed applications on [subdomain].[Values.domain]/proxy/[name]. Useful to avoid CORS requests from frontend clients
  - `readinessProbe`: defines a a url to use as a readiness probe
  - `livenessProbe`: defines a a url to use as a liveness probe
  - `dockerfile`: configuration for the dockerfile, currently only implemented in Skaffold
    - `buildArgs`: a map of build arguments to provide to the dockerfile when building with Skaffold

# Example code
- [Sample application](../../applications/samples) is a sample web application providing working examples of deployment configuration, backend and frontend code.
    

