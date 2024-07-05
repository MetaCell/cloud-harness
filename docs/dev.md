# CloudHarness, developer documentation

This documentation is meant to be read by developers that needs to make modifications in CloudHarness.
The goal of this doc is to show how CloudHarness is internally built, the different parts of the code/files that are relative to specific features, and to provide a map to be able to modify or implement new features quickly.

CloudHarness is a project that allows you to: quickly generate the code of your webapp, considering that it runs in the cloud with a micro-service architecture, and to easily connect all those micro-services together to finally build the final app.
Currently, the tools that CloudHarness can consider to build the final app are the following:

* [OpenAPI](https://www.openapis.org/) for generating the model and API of your application (based on an OpenAPI specification),
* [KeyCloak](https://www.keycloak.org/) for the authentication,
* [Argo Workflow](https://argoproj.github.io/argo-workflows/) for orchestrating Kubernete workflows. You can consider Kunernete workflows with Argo as specific actions that needs to be executed in a isolated environement as it requires more resources or can take time. Usually they are started after a user action.
* [Kafka](https://kafka.apache.org/documentation/) to stream the events from each micro-services and notify listeners that a micro-service or a workflow finished its work,
* [Sentry](https://docs.sentry.io/) to report and log errors and run time exceptions,
* [JupyterHub](https://jupyter.org/hub) to provide jupyter notebooks access to a group of users,
* [Volume Manager](../applications/volumemanager/) to deal with external file system,
* [NFS Server](../applications/nfsserver/) to provide storage of file on an external NFS file system,
* [Kubernete](https://kubernetes.io/) is used to manage the auto-scaling, deployements, ... of micro-services on a cluster,
* [Code Fresh](https://codefresh.io/) for the remote build of the application, and it is configured to initiate a deployment on a remote Kubernete cluster,
* [Helm Chart](https://helm.sh/docs/topics/charts/) for the packaging of Kubernete resources to simplify the deployment of the application,
* [Skaffold](https://skaffold.dev/) to help deploying the packaged application in a Kubernete cluster.

CloudHarness is made of two major parts:

1. a command line interface (CLI) that helps bootstrapping the infrastructure for a dedicated tool or project,
2. a runtime which provides several helpers and already pre-coded services to handle the different micro-services.

## The CloudHarness CLI

The command line interface is used to generate various aspects of your webapp.
Basically, the CloudHarness CLI can generate (depending on your command line option):

1. the skeleton (the various directory and stub files) for your webapp, depending on your needs, *e.g.:* a Django-based backend and a React-based frontend,
2. the base configuration files for Code Fresh: `codefresh-XXX.yaml` files,
3. the Helm Chart files for packaging your app,
4. the skaffold configuration file `skaffold.yaml`,
5. the copy of different pre-coded micro-services if required, *e.g.:* micro-service for authentication, based on KeyCloak, ...
6. the SSL certificate.

The CloudHarness CLI project is located in [`tools/deployment-cli-tools`](../tools/deployment-cli-tools).
The source code of the project is located in [`tools/deployment-cli-tools/ch_cli_tools`](../tools/deployment-cli-tools/ch_cli_tools).
The code is organized around the idea that there is a module by artifact that can be generated:

```bash
deployment-cli-tools
├── ch_cli_tools
│   ├── codefresh.py          # Code Fresh configuration generation
│   ├── helm.py               # Helm chart files generation
│   ├── __init__.py           # Defines logging level and some global constants
│   ├── models.py             # Currently empty file
│   ├── openapi.py            # Generates the model and API part of your model (back and front) depending on an OpenAPI specification
│   ├── preprocessing.py      # Provide some function to readapt/preprocess paths for the Helm generation
│   ├── scripts
│   │   ├── bootstrap.sh      # Shell script for generating certificates for the app depending on the domain name
│   ├── skaffold.py           # Skaffold configuration script generation
│   └── utils.py              # Set of utils that are use to deal with directory/dict merging, path search, ...
├── harness-application       # The main entry/script to create the base application and generate the base code from the OpenAPI specification(skeleton)
├── harness-deployment        # The main entry/script to create the deployement for the application, based on some CloudHarness configuration files
├── harness-generate          # The main entry/script to (re-)generate the base code for the frontend/backend from the OpenAPI specification, without crating folders for the application
└── tests/*                   # The tests folder for the CLI tools
```

### Generation of the base application skeleton

The generation of the base application skeleton is obtain through the [`harness-application`](../tools/deployment-cli-tools/harness-application) command.
The command parses the type of application that needs to be generated.
If a new generator for a type of application needs to be defined, the main function of the script should be modified.

The generation of the application is done in two times.
First the skeleton of the application is generated (the directories, basic files), then the code of REST application (server and client) is generated from the OpenAPI specification.
The following code fragment from the `harness-application` script shows how the skeleton is produced:

```python
if "django-app" in args.templates and "webapp" not in templates:
        templates = ["base", "webapp"] + templates
    for template_name in templates:
        if template_name == 'server':
            with tempfile.TemporaryDirectory() as tmp_dirname:
                copymergedir(os.path.join(CH_ROOT, APPLICATION_TEMPLATE_PATH, template_name), tmp_dirname)  # <1>
                merge_configuration_directories(app_path, tmp_dirname)
                generate_server(app_path, tmp_dirname)
        for base_path in (CH_ROOT, os.getcwd()):
            template_path = os.path.join(base_path, APPLICATION_TEMPLATE_PATH, template_name)
            if os.path.exists(template_path):
                merge_configuration_directories(template_path, app_path)  # <1>
```

First, if `django-app` is defined as a template for the application, and the `webapp` template is not set, then `base` and `webapp` are added to the list of templates.
Then, depending on the template name, a template directory is merged with the code of the application that will be developed (if it exists), as seen in `<1>`.
The templates for each type of application is described by the constant `APPLICATION_TEPLATE_PATH` and points to [`application-templates`](../application-templates/).
Based on the name of the template used for the application generation, the actual template with the same name is searched in this path, and copied/merged in the application target folder.
The constant, as well as many other constants, are located in [`cloudharness_utils.constants`](../libraries/cloudharness-utils/cloudharness_utils/constants.py).
This file is part of the CloudHarness runtime.
Other constants are located there as shown in the following code extract.

```python
APPLICATION_TEMPLATE_PATH = 'application-templates'
# ...
APPS_PATH = 'applications'
DEPLOYMENT_PATH = 'deployment'
CODEFRESH_PATH = 'codefresh/codefresh.yaml'
# ...
CH_BASE_IMAGES = {'cloudharness-base': 'python:3.9.10-alpine', 'cloudharness-base-debian': 'python:3.9.10'}
# ...
```

Those constants defines several aspects of CloudHarness.
For example, we can see there what base Docker image will be considered depending on what's configured for your application, where will be located the deployment files, from where the applications to generate/pick should be generated, where are located the templates for each kind of generation target, as well as where the configuration for codefresh should be looked for.

Once the skeleton of the application is generated considering some templates, the code of the REST API is generated from the OpenAPI specification.
The generation relies on two functions: `generate_server` and `generate_fastapi_server` and `generate_ts_client`.
Those functions are defined in the [`openapi.py`](../tools/deployment-cli-tools/ch_cli_tools/openapi.py) module.
This module and those functions use `openapi-generator-cli` to generate the code for the backend and/or the frontend.
With this generation, and depending on the templates used, some fine tuning or performed in the code/files generated.
For example, some placeholders are replaced depending on the name of the application, or depending on the module in which the application is generated.

#### How to extend it?

Here is some scenarios that would need to modify or impact this part of CloudHarness:

**A new template for a directory/file skeleton needs to be added**. In this case, if a new template needs to be added, there is various operations that needs to be performed:

1. a new template folder with the basic skeleton for the application needs to be created in [`applications-templates`](../application-templates/) with the name that the template should have as CLI argument,
2. modify the [`harness-application`](../tools/deployment-cli-tools/harness-application) script to include the new template,
3. add, if necessary, a new function in [`openapi.py`](../tools/deployment-cli-tools/ch_cli_tools/openapi.py) to deal with the generation of the API REST code depending on your new template,
4. alter, if necessary, the configuration files that are generated in the [`harness-application`](../tools/deployment-cli-tools/harness-application) script.

**Change/add the application base images**. In this case, if a new base image, or an existing base image should be modified, then the dictionnary located in [`constants.py`](../libraries/cloudharness-utils/cloudharness_utils/constants.py) should be extended/modified.

### Generation of the base application skeleton

The (re-)generation REST API is obtain through the [`harness-generate`](../tools/deployment-cli-tools/harness-generate) command.
The command parses the name of the application, gets the necessary dependencies (the java OpenAPI generator cli), and generates the REST model, the servers stubs and well as the clients code from the OpenAPI specifications.

The generation of the REST model is done by the `generate_model(...)` function, the generation of the server stub is done by the `generate_servers(...)` function, while the clients generation is done by the `generate_clients(...)` function.
All of these functions are located in the `harness-generate` script.

Under the hood, the `generate_servers(...)` function uses the `generate_fastapi_server(...)` and the `generate_server(...)` function that are defined in the [`openapi.py`](../tools/deployment-cli-tools/ch_cli_tools/openapi.py) module.
The generation of one type of servers over another one is bound to the existence of a `genapi.sh` file:

```python
def generate_servers(root_path, interactive=False):
    # ...
    if os.path.exists(os.path.join(application_root, "api", "genapi.sh")):
        # fastapi server --> use the genapi.sh script
        generate_fastapi_server(application_root)
    else:
        generate_server(application_root)
```

The `generate_clients(...)` function also uses `generate_python_client(...)` and `generate_ts_client(...)` from the [`openapi.py`](../tools/deployment-cli-tools/ch_cli_tools/openapi.py) module.
The `generate_ts_client(...)` function is called only if there is folder named `frontend` in the application directory structure:

```python
def generate_clients(root_path, client_lib_name=LIB_NAME, interactive=False):
    # ...
    app_dir = os.path.dirname(os.path.dirname(openapi_file))
    generate_python_client(app_name, openapi_file,
                           client_src_path, lib_name=client_lib_name)
    if os.path.exists(os.path.join(app_dir, 'frontend')):
        generate_ts_client(openapi_file)
```

### Generation of the application deployment files

The generation of the deployment files is obtain through the [`harness-deployment`] script.
The script uses various arguments to configure properly the deployment of the application as well as some debug configuration helper for vscode as shown in the snippet below:

```python
helm_values = create_helm_chart(  # <1>
    root_paths,
    tag=args.tag,
    registry=args.registry,
    domain=args.domain,
    local=args.local,
    secured=not args.unsecured,
    output_path=args.output_path,
    exclude=args.exclude,
    include=args.include,
    registry_secret=args.registry_secret,
    tls=not args.no_tls,
    env=envs,
    namespace=args.namespace
)

merged_root_paths = preprocess_build_overrides(
    root_paths=root_paths, helm_values=helm_values)  # <2>

if not args.no_cd_gen and envs:
    create_codefresh_deployment_scripts(  # <3>
        merged_root_paths,
        include=args.include,
        exclude=args.exclude,
        envs=envs,
        base_image_name=helm_values['name'],
        helm_values=helm_values)

# ...

create_skaffold_configuration(merged_root_paths, helm_values)  # <4>

#...

hosts_info(helm_values)  # <5>
```

First, the code for the Helm chart files is generated using the `create_helm_chart(...)` function (`<1>`).
Then, the dictionnary of values for the Helm configuration is preprocessed to change some path (`<2>`).
If necessary, the codefresh deployment scripts are generated (`<3>`) using the `create_codefresh_deployment_scripts(...)` function.
Then, the skaffold configuration is generated using the dictionnary generated for the Helm configuration and the `create_skaffold_configuration(...)` function (`<4>`).
Finally, the information about the host IP, domain names, ... is displayed on stdout using the `hosts_info(...)` function (`<5>`).

#### Generation of the Helm chart

The generation of the Helm chart relies on the `create_helm_chart(...)` function which is located in the [`helm.py`](../tools/deployment-cli-tools/ch_cli_tools/helm.py) module.

This function creates an instance of `CloudHarnessHelm` and processes the values inserted in this instance. The `process_values(...)` method on the `CloudHarnessHelm` class creates the result dictionnary with all the required keys and finally returns them wrapped in an instance of [`HarnessMainConfig`](../libraries/models/cloudharness_model/models/harness_main_config.py).
This class extracts information from the dictionnary and gives quick access to them through specific getter/setters (this code, as well as the code located in [`cloudharness_model/models/`](../libraries/models/cloudharness_model/models/) is actually generated from the OpenAPI specification of the CloudHarness concepts located in [`cloudharness_model/api/openapi.yaml`](../libraries/models/api/openapi.yaml), which contains details about the different keys and concepts that can be used for a basic CloudHarness application configuration).
The intermediate dictionnary created for the Helm chart generation is complex and contains many sub-dictionnaries that all capture a part of the Helm chart.
The initializer receives as arguments information about the application, its location, the namespace of the application when it will run in Kubernete, ..., processes the information, creates the dictionnary and save the results as a YAML file using the `merge_to_yaml_file(...)` from the [`utils.py`](../tools/deployment-cli-tools/ch_cli_tools/utils.py) module to the path partially specified by constants from the `constants.py` module.

The `helm.py` module also defines the `hosts_info(...)` function that displays information about the domain, subdomains, IP, ... of the application to be deployed.

#### Generation of the Codefresh deployment files

The generation of the Codefresh deployement files is entirely done from the [`codefresh.py`](../tools/deployment-cli-tools/ch_cli_tools/codefresh.py) module using the `create_codefresh_deployment_scripts(...)` function.
This function takes as parameter the Helm configuration generated by the `create_helm_chart(...)` function and generates different codefresh deployment script depending on environments (*e.g.:* dev, stage, prod).


#### Generation of the skaffold configuration

The skaffold configuration is generated by the `create_skaffold_configuration(...)` function from the [`skaffold.py`](../tools/deployment-cli-tools/ch_cli_tools/skaffold.py) module.
This function also generates the skaffold entries for the Dockerfiles of the micro-services used in the application.
The skaffold generation is based on the [`skaffold-template.yaml`](../deployment-configuration/skaffold-template.yaml) from the CloudHarness project located in [`deployment-configuration`](../deployment-configuration/).
This base configuration is merged with the configuration dedicated to a specific project and which is located in the `deployment-configuration` folder of the project.
Finally, once all the requiered information is injected in the skaffold configuration dictionnary, the dictionnary is saved as a YAML file in the `deployment/skaffold.yaml` file in the project directory.

#### How to extend the deployment generation

**Add a new configuration deployment system**. If a new configuration system is targeted by the generation (not Helm chart or skaffold), a new kind of configuration should be added to CloudHarness, and the code should be rewritten to produce a configuration dictionnary from a new file that is not `Chart.yaml`, or that is compatible with this one.
This new kind of argument should be parsed from the command line in the `harness-configuration` script to take into account the new target.
A new module should be added where `helm.py` and `skaffold.py` are located.
This new module should be responsible for taking information from the application dictionnary and use this information to generate a new dictionnary in memory with the missing information that are necessary to properly build the deployment scripts.
Finally, new unit tests should be added to the [deployment-cli-tools/tests](../tools/deployment-cli-tools/tests/) folder.
If a new kind of class must be coded to get all the information of the configuration (like the `CloudHarnessHelm` class), then the [`cloudharness_model/api/openapi.yaml`](../libraries/models/api/openapi.yaml) must be modified to introduce the new type of object that will be manipulated to represent the documentation, and the OpenAPI model should be generated again.


## The CloudHarness runtime

The CloudHarness runtime is located in the [`libraries`](../libraries/) folder.
The runtime library defines a set of concepts and functions to help the various micro-services to communicate together.
The code is organised as such:

```bash
libraries/
├── api                      # Contains the CloudHarness OpenAPI specification
│   ├── config.json          # A configuration file to direct the OpenAPI code generation
│   └── openapi.yaml         # The OpenAPI specification
├── client                   # A Python client to access the CloudHardness API
│   └── cloudharness_cli     # The programmatic Python client API to access CloudHarness. This code is generated
├── cloudharness-common      # The runtime library in itself that is used for dedicated tasks and applications
├── cloudharness-utils       # Some shared utils between the CloudHarness CLI tools and the runtime (constants.py)
└── models                   # The CloudHarness model (generated from the OpenAPI specification)
    ├── api                  # Copy of the artifacts that have been used for the generation (from libraries/api)
    │   ├── config.json
    │   └── openapi.yaml
    └── cloudharness_model   # The generated CloudHarness Python model
```

The `cloudharness-common` folder is where is located most of the custom code for the various tasks and applications.
The code is structured as this:

```bash
cloudharness
├── applications.py          # Contains helpers regarding about the application configuration
├── auth                     # Primitives related to authentication and KeyCloak
│   ├── exceptions.py        # Dedicated exceptions
│   ├── __init__.py
│   ├── keycloak.py          # Implementation specific code for KeyCloak, contains helpers to create KeyCloak clients, get tokens, configuration, ...
│   └── quota.py             # Manage a quota by users
├── errors.py                # Dedicated exceptions
├── events                   # Primitives related to event streaming with Kafka
│   ├── client.py            # Functions related to the connexion to the Kafka broker
│   ├── decorators.py        # Decorator implementation to easily send the result of a function to Kafka
│   ├── __init__.py
├── infrastructure           # Primitives related to the management of the infrastructure with Kubernete
│   ├── __init__.py
│   ├── k8s.py               # Functions for Kubernete namespace and pod managment
├── __init__.py
├── middleware               # Manage user authentication header injection
│   ├── django.py            # Way of injecting the auth token in requests for Django
│   ├── flask.py             # Way of injecting the auth token in requests for Flask
│   ├── __init__.py
├── sentry                   # Primitives for sentry initialisation
│   └── __init__.py
├── service                  # Additional services to handle Persistent Volum Claim in Kubernetes
│   ├── __init__.py
│   ├── pvc.py
│   └── templates
│       └── pvc.yaml
├── utils                    # Set of helpers
│   ├── config.py            # Helper class for the CloudHarness configuration
│   ├── env.py               # Helper for the env variables in configurations
│   ├── __init__.py
│   ├── secrets.py           # Helper class for the CloudHarness application secrets
│   ├── server.py            # Helpers for flask/server bootstrapping
└── workflows                # Primitives for the management of workflows
    ├── argo.py              # Helpers and function to access the Argo REST API
    ├── __init__.py
    ├── operations.py        # Functions to create new Argo operations
    ├── tasks.py             # Functions to create new Argo tasks
    └── utils.py             # Helpers to get information from the pods that executes operations and tasks
```