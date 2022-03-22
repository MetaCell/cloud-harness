<p align="center">
<img src="https://github.com/MetaCell/cloud-harness/blob/develop/cloudharness.png?raw=true" alt="drawing" width="200"/>
</p>

CloudHarness is a base infrastructure facilitator for microservice based applications deployed on Kubernetes.
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
    - secrets
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

# Get started

## Prerequisites

### Operative system

Cloudharness can be used on all major operative systems.
- Linux: supported and tested
- MacOS: supported and tested
- Windows/WSL2: supported and tested
- Windows native: mostly working, unsupported  

### Python
Python 3.7-3.9 must be installed.

It is recommended to setup a virtual environment.
With conda: 
 ```bash
 conda create --name ch python=3.7
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

## CloudHarness command line tools
To use the cli tools, install requirements first:

```bash
source install.sh
```
### Generate deployment

To generate a deployment, run `harness-deployment`. See [below](#Deployment) for more.

### Create new REST application
To create a new REST application, run `harness-application` from the root of your solution.

### Generate server and client code from openapi
To (re)generate the code for your applications, run `harness-generate` from the root.
The script will look for all openapi applications, and regenerate the Flask server code and documentation.
Note: the script will eventually override any manually modified file. To avoid that, define a file openapi-generator-ignore.

# Extend CloudHarness to build your solution
CloudHarness is born to be extended. In order to extend CloudHarness you just need to mirror the folder structure:
* **applications**: place here your custom applications, or override default ones
* **deployment-configuration**: override the helm chart default values and templates
* **infrastructure**: define base images to use in your application

or simply copy the *blueprint* folder.

# Build and deploy

The script `harness-deployment` scans your applications and configurations to create the build and deploy artifacts.
Created artifacts include:
 - Helm chart
 - Skaffold build and run configuration
 - Visual Studio Code debug and run configuration
 - Codefresh pipeline yaml specification (optional)

With your solution folder structure looking like

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
See the dedicated [Build and deploy](./docs/build-deploy-howto.md) document for more details and examples.

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


[![Codefresh build status]( https://g.codefresh.io/api/badges/pipeline/tarelli/Cloudharness%2Funittests?type=cf-1&key=eyJhbGciOiJIUzI1NiJ9.NWFkNzMyNDIzNjQ1YWMwMDAxMTJkN2Rl.-gUEkJxH6NCCIRgSIgEikVDte-Q0BsGZKEs4uahgpzs)]( https://g.codefresh.io/pipelines/edit/new/builds?id=6034cfce1036693697cd602b&pipeline=unittests&projects=Cloudharness&projectId=6034cfb83bb11c399e85c71b)
