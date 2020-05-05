<p align="center">
<img src="https://github.com/MetaCell/cloud-harness/blob/develop/cloudharness.png?raw=true" alt="drawing" width="200"/>
</p>

# CloudHarness
CloudHarness is a base infrastructure facilitator for micro-service based applications deployed on Kubernetes.

What building your cluster application with CloudHarness gives to you:
* Common framework and utilities to develop and deploy micro-service application
  * REST-API scaffolding building based on OpenApi (Python-Flask)
  * Helm chart automatic generation
  * Automatic build and push of images
  * Continuous deployment script generation (Codefresh)
* Prebuilt support applications and shared library to:
  * Log in and user management - based on Keycloak
  * Submit batch and asynchronous workflows - based on Argo
  * Orchestrate Micro-services - based on Kafka

## Get started

### Prerequisites

Python 3.7+ must be installed.

It is recommended to setup a virtual environment.
With conda: 
 ```bash
 conda create --name ch python=3.7
 conda activate ch
 ```

Install requirements:

```bash
pip install -r requirements.txt
```
### Generate deployment

To generate a deployment, run either `harness-deployment` or `harness-codefresh` depending on the type of deployment you
like. See [below](#Deployment) to know more.

### Create new REST application
To create a new REST application, run `harness-application` from the root.

### Generate server and client code from openapi
To (re)generate the code for your applications, run `harness-generate` from the root.
The script will look for all openapi applications, and regenerate the Flask server code and documentation.
Note: the script will eventually override any manually modified file. To avoid that, define a file openapi-generator-ignore.

## Extend CloudHarness
CloudHarness is born to be extended. In order to extend CloudHarness you just need to mirror the folder structure:
* **applications**: place here your custom applications, or override default ones
* **deployment-configuration**: override the helm chart default values and templates
* **infrastructure**: define base images to use in your application

or simply copy the *blueprint* folder

## Deployment



### Manually deploy on a kube cluster
The Kubernetes client `kubectl` must be set up and working on the local machine,
for instance with a Google Cloud cluster or a local Minikube.

1. Locally build the images with `harness-deployment -b -l
[--registry localhost:5000] [--tag 0.0.1]`
1. Create the namespace `kubectl create ns ch`
1. Create the namespace `kubectl create ns argo-workflows`
1. (Optional) Try the helm chart with `helm install helm --name ch --namespace ch --dry-run`
1. Install the helm chart with `helm install --name=ch deployment/helm  --namespace ch` (`helm install ch helm  --namespace ch` on helm 3)
1. Install Argo (see below)

To upgrade an already existing chart, run
`helm upgrade ch deployment/helm --namespace ch --install --force --reset-values`

### Continuous deployment with Codefresh
The codefresh pipeline setup is provided in `codefresh/codefresh.yaml`.
The pipeline will take care of building the images from the source code and deploy the helm chart.
Log in to codefresh and run the pipeline associated to the repository.
To setup a new pipeline, simply indicate the remote yaml path `deployment/codefresh/codefresh.yaml`

In order to update the deployment, run
```
harness-codefresh .
```
More information about how to run the script below

### Relevant files and directory structure
Deployment files are automatically generated with the script 
`harness-deployment`.

all the resources intended to install and deploy the platform on Kubernetes.
 - `codefresh`: codefresh build related files (automatically generated)
 - `deployment-configuration`: override deployment templates

What this script does is to go through all the defined applications and use templates to define all the required 
definitions and variables.

General templates are defined inside `deployment-configuration`.

Applications can override templates values by defining a file `values.yaml` in the same directory of the Docker file.

#### Note: Docker registry
With the `--build` flag we are locally building the images. In order to make the deploy work, we need to specify a 
registry that is visible from inside the cluster. The parameter `--registry` allows to specify a registry in which 
images are pushed after the build.
Any public registry will work. The suggested way to go is to install a registry on localhost:5000 inside
the kube cluster and push on that registry, also forwarded to localhost.

On minikube can use the registry addon:

`minikube addons enable registry`

Then forward with:
`kubectl port-forward --namespace kube-system $(kubectl get po -n kube-system | grep registry | grep -v proxy | \awk '{print $1;}') 5000:5000`

### Argo installation

Argo is not yet part of the helm chart

In order to install it in the cluster, run

```
kubectl create ns argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/v2.4.3/manifests/install.yaml
kubectl apply -f argo/argo-service-account.yaml -n argo-workflows
kubectl create rolebinding argo-workflows --clusterrole=admin --serviceaccount=argo-workflows:argo-workflows -n argo-workflows
```

See also https://argoproj.github.io/docs/argo/demo.html#2-install-the-controller-and-ui



### Details about deployment generation

The following deployment files are generated by `harness-deployment`:

- Helm chart configuration for custom deployment: **./helm/values.yaml**
- Codefresh build and deploment definition: **./codefresh/codefresh.yaml** 

The script `harness-codefresh` generates a build script to be used by codefresh.

The control on the content of those files can be achieved primarily by setting up a
custom `values.yaml` and deploy/templates in the application folder.
The files under
`deployment-configuration` can be also modified for general overrides.

Things to notice:

- Each image created during the build step will have to be deployed to a k8s cluster.
- A Helm chart was created under `deployment/helm` path to handle deployments.
- To populate the chart we use a `values.yaml` file.
- Depending on whether we want to deploy to minikube or GKE a slightly different file is required.
- `harness-deployment` handles the creation of both files at ones.

How to:

- Add a file named `values.yaml`  to the application and put some values on it.
- Run `harness-deployment`
- Check `./deployment/codefresh/codefresh.yaml` and `./deployment/helm/ch/values.yaml`

For example:

```yaml
# ./applications/docs/values.yaml
harvest: false
enabled: true
port: 8080
subdomain: docs
```

Will generate entries in the following files:

1

```yaml
# ./deployment/helm/ch/values.yaml
docs:
  enabled: true
  harvest: false
  image:
    name: ch-docs
    tag: 0.0.1
  name: docs
  port: 8080
  subdomain: docs
```

2

```yaml
# ./deployment/codefresh/values.yaml
docs:
  enabled: true
  harvest: false
  image:
      name: ch-docs
      tag: ${{CF_SHORT_REVISION}}-${{CF_BUILD_TIMESTAMP}}
  name: ch-docs
  port: 8080
  subdomain: docs
```

3 Ingress entry is generated if subdomain is specified:
```yaml
  - host: "docs.cloudharness.metacell.us"
    http: 
      paths:
      - path: /
        backend:
          serviceName: "docs"
          servicePort: 8080
```

### Build

The script `harness-deployment` allows to optionally build the
 application's Docker images. Those Docker images are needed if we plan to deploy 
outside Codefresh, for instance for local testing with Minikube.

#### How to build

Run `harness-deployment -b -l` (all images are built unless `-i` option is provided).

For further information, run `harness-deployment --help`



#### Build conventions

The build script scans inside `./applications` for dockerfile definitions. It walks `application` folder recursively and creates a docker image for each dockerfile it finds.

Name convention for the images is as follows:

`./application/some-folder/anotherone/a-third-one/Dockerfile` -> `some-folder-anotherone-a-third-one`

The `src` folder is removed from the final image name.

## How to add a new CloudHarness custom application

1. Add the application inside `applications/[APPLICATION_NAME]` with a Dockerfile in it
1. Define *deploy/values.yaml* inside the file in order to specify custom values for the application
1. (optional) define specific helm templates on *deploy/values.yaml*
1. Run `harness-deployment`
1. Define the helm templates for the application inside `deploy/templates`. In the helm template, it is recommended to use the automatically generated values `helm/ch/values.yaml`

See more about the Helm chart installation in the specific [README](utilities/cloudharness-deploy/README.md).


## How to add an external application

A CloudHarness application can specify a Kubernetes deployment also using externally defined public images.
Create a new CloudHarness application with the helm templates inside the *deploy* subdirectory 


