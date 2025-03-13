<p align="center">
<img src="https://github.com/MetaCell/cloud-harness/blob/develop/cloudharness.png?raw=true" alt="drawing" width="200"/>
</p>

CloudHarness is a base infrastructure facilitator for microservice based applications deployed primarily on Kubernetes.
Can scaffold and maintain your cloud solution on top of Cloudharness without writing
Kubernetes templates, with in place common utilities and applications already configured for you.

What building your cloud solution with CloudHarness gives to you:

- Common framework and utilities to develop and deploy micro-service application

  - Helm chart automatic generation
    - deployments
    - services
    - ingress configuration
    - databases
    - backup cron jobs
    - access gatekeepers configuration
    - secrets
    - templated config maps from files
  - Docker compose configuration generation
    - services
    - traefik configuration
    - databases (postgreql)
    - access gatekeepers configuration
    - secrets and configmaps

  * Automatic build and push of images
  * REST-API scaffolding building based on OpenApi
  * Continuous deployment script generation
  * Debug backend applications running on Kubernetes
  * Python cluster access utilities

* Prebuilt support applications and shared library to:
  * Log in and user management - based on Keycloak
  * Submit batch and asynchronous workflows - based on Argo
  * Orchestrate microservices - based on Kafka
  * Assign compute workspaces to users - based Jupyterhub
* Testing framework to help you write and run tests
  * Unit tests
  * API integration tests
  * End to End tests (with Puppeteer)
* CI/CD pipelines generation

# Why CloudHarness?

The microservice architecture is a great to get code separation and flexible development, but may not be of easy implementation, especially for small development teams/projects.
In particular, these questions may rise:

- How do I create a deployment for my microservices?
- How do I orchestrate my microservices?
- How to create consistent api documentation?
- Do I need to be an experienced devops to create a micro-service based application?
- Wouldn't it be nice to develop a plain database/backend/frontend application without infrastructure boilerplate but still be able to configure everything I want when needed?
- How to run batch operations like ETL processes easily and efficiently in a cloud environment?
- How to manage databases without being locked to a specific vendor solution?
- How to perform database backups?
- How to manage secret data?
- What about having a precounfigured account management application?
- Sooner rather than later I'll need an orchestration queue. Why not have that just ready to use?

# Command line tools

CloudHarness provides the following command line tools to help application scaffolding and deployment.

* `harness-deployment` - generate the helm chart to deploy on Kubernetes.
* `harness-application` - create a new CloudHarness REST application.
* `harness-generate` - generates server and client code for all CloudHarness REST applications.
* `harness-test` - run end to end tests

# Get started

## Prerequisites

### Operative system

Cloudharness can be used on all major operative systems.

- Linux: supported and tested
- MacOS: supported and tested
- Windows/WSL2: supported and tested
- Windows native: mostly working, unsupported

### Python

Python 3.10 must be installed.

It is recommended to setup a virtual environment.
With conda:

```bash
conda create --name ch python=3.10
conda activate ch
```

### Docker

[Docker](https://www.docker.com) is required to build locally.

### Kubernetes command line client

[kubectl](https://kubernetes.io/docs/tasks/tools/) allows you to connect to your Kubernetes cluster or local environment.

### Helm

[Helm](https://helm.sh/docs/intro/install/) is required to deploy to your Kubernetes cluster or local environment.

### Skaffold

[Skaffold](https://skaffold.dev/docs/install/) is the way to go to build and debug your application in your local development environment.

### Docker compose

[Docker Compose](https://docs.docker.com/compose/) is required if the docker compose system is the target (instead of Kubernetes).

### Node environment

A node environment with npm is required for developing web applications and to run end to end tests.

Recommended:

- node >= v14.0.0
- npm >= 8.0.0

### Java Runtime Environment

A JRE is needed to run the code generators based on openapi-generator.

For more info, see [here](https://openapi-generator.tech/docs/installation).

## CloudHarness command line tools

To use the cli tools, install requirements first:

```bash
bash install.sh
```

### Create new REST application

`harness-application` is a command-line tool used to create new applications based on predefined code templates. It allows users to quickly scaffold applications with backend, frontend, and database configurations.

#### harness-application Usage

```sh
harness-application [name] [-t TEMPLATE]
```

#### harness-application Arguments

- `name` *(required)* – The name of the application to be created.

#### harness-application Options

- `-h, --help` – Displays the help message and exits.
- `-t TEMPLATES, --template TEMPLATES` – Specifies one or more templates to use when creating the application.

#### Available Templates

The following templates can be used with the `-t` flag:

- **flask-server** – Backend Flask server based on OpenAPI.
- **webapp** – Full-stack React web application with both frontend and backend.
- **db-postgres** – PostgreSQL database setup.
- **db-neo4j** – Neo4j database setup.
- **db-mongo** – MongoDB database setup.
- **django-fastapi** – FastAPI and Django backend based on OpenAPI.
- **django-ninja** – Django Ninja backend.

#### harness-application Examples

##### Create a New Flask-Based Microservice Application

```sh
harness-application myapp
```

##### Create a Full-Stack Web Application

```sh
harness-application myapp -t webapp
```

##### Create a Web Application with Mongo Database

```sh
harness-application myapp -t webapp -t db-mongo
```

##### Display Help Information

```sh
harness-application --help
```

#### harness-application Notes

- Multiple templates can be specified concatenating the -t parameter.
- The tool generates the necessary scaffolding for the chosen templates.
- Ensure you have the required dependencies installed before running the generated application.
- For more information, run `harness-application --help` or check out the additional documentation:
  - [Applications README](./docs/applications/README.md)
  - [Developer Guide](./docs/dev.md)

### Generate server and client code from openapi

To (re)generate the code for your applications, run `harness-generate`.
`harness-generate` is a command-line tool used to generate client code, server stubs, and model libraries for applications. It walks through the filesystem inside the `./applications` folder to create and update application scaffolding. The tool supports different generation modes and allows for both interactive and non-interactive usage.

#### Usage

```sh
harness-generate [mode] [-h] [-i] [-a APP_NAME] [-cn CLIENT_NAME] [-t | -p] [path]
```

#### harness-generate Arguments

- `path` *(optional)* – The base path of the application. If provided, the `-a/--app-name` flag is ignored.

#### harness-generate Options

- `-h, --help` – Displays the help message and exits.
- `-i, --interactive` – Asks for confirmation before generating code.
- `-a APP_NAME, --app-name APP_NAME` – Specifies the application name to generate clients for.
- `-cn CLIENT_NAME, --client-name CLIENT_NAME` – Specifies a prefix for the client name.
- `-t, --ts-only` – Generates only TypeScript clients.
- `-p, --python-only` – Generates only Python clients.

#### Generation Modes

`harness-generate` supports the following modes:

- **all** – Generates both server stubs and client libraries.
- **clients** – Generates only client libraries.
- **servers** – Generates only server stubs.
- **models** – Regenerates only model libraries.

#### harness-generate Examples

##### Generate Client and Server stubs for all applications

```sh
harness-generate all
```

##### Generate Client and Server stubs for a Specific Application

```sh
harness-generate all -a myApp
```

##### Generate Only Client Libraries

```sh
harness-generate clients
```

##### Generate Only Server Stubs

```sh
harness-generate servers
```

##### Regenerate Only Model Libraries (deprecated)

```sh
harness-generate models
```

##### Generate TypeScript Clients Only and Server stubs

```sh
harness-generate all -t
```

##### Generate Python Clients Only and Server stubs

```sh
harness-generate all -p
```

##### Interactive Mode

```sh
harness-generate all -i
```

#### harness-generate Notes

- The tool scans the `./applications` directory for available applications.
- If `path` is provided, `-a/--app-name` is ignored.
- The `models` mode is a special flag used when regenerating only model libraries (deprecated).
- The tool supports interactive mode to confirm before generating clients.
- Use either `-t` or `-p`, but not both simultaneously.

For further details, run:

```sh
harness-generate --help
```

### Generate deployment

To generate a deployment, run `harness-deployment`. See [below](#build-and-deploy) for more information.

# Extend CloudHarness to build your project

CloudHarness is born to be extended.

The quickest way to start is to install Cloud Harness, copy the *blueprint* folder and build from that with the cli tools, such as
`harness-application`, `harness-generate`, `harness-deployment`.

See the [developers documentation](docs/dev.md#start-your-project) for more information.

# Build and deploy

The script `harness-deployment` scans your applications and configurations to create the build and deploy artifacts.
Created artifacts include:

- Helm chart (or docker compose configuration file)
- Skaffold build and run configuration
- Visual Studio Code debug and run configuration
- Codefresh pipeline yaml specification (optional)

With your project folder structure looking like

```
applications
deployment-configuration
infrastructure
cloud-harness
```

run

```
harness-deployment cloud-harness . [PARAMS]
```

to create the build and deployment artifacts for your solution.
See the dedicated [Build and deploy](./docs/build-deploy/README.md) document for more details and examples.

# Add and manage applications

Any Dockerfile added in a subfolder below the [applications](./applications) directory is interpreted as an application part of the deployment.
The `harness-application` cli tool creates new applications from predefinite code templates.
See the dedicated [Applications](./docs/applications) documents for more details and examples.

# Configure the deployment

First, create the folder `deployment-configuration` on project level.

Then, you can selectively add files related to configuration that you want to personalize:

- `values-template.yaml`: base for `helm/<chart-name>/values.yaml`. Modify this file to add values related to new infrastructure elements not defined as an application
- `value-template.yaml`: cloud-harness application configuration inside `values.yaml`. Prefer adding a custom `values.yaml` to your application over changing this file.
- `codefresh-template-dev.yaml`: base for `codefresh/codefresh-dev.yaml`. Modify this file if you want to change the build and deploy steps in the codefresh dev pipeline
- `codefresh-template-prod.yaml`: base for `codefresh/codefresh-prod.yaml`. Modify this file if you want to change the deploy and publish steps in the codefresh production pipeline. The production pipeline is meant to reause the same set of images from a previously completed dev pipeline.
- `codefresh-build-template.yaml`: base for a single build entry in `codefresh.yaml`

For more information about how to configure a deployment, see [here](./build-deploy/helm-configuration.md)

[![Codefresh build status](https://g.codefresh.io/api/badges/pipeline/tarelli/Cloudharness%2Funittests?type=cf-1&key=eyJhbGciOiJIUzI1NiJ9.NWFkNzMyNDIzNjQ1YWMwMDAxMTJkN2Rl.-gUEkJxH6NCCIRgSIgEikVDte-Q0BsGZKEs4uahgpzs)](https://g.codefresh.io/pipelines/edit/new/builds?id=6034cfce1036693697cd602b&pipeline=unittests&projects=Cloudharness&projectId=6034cfb83bb11c399e85c71b)
