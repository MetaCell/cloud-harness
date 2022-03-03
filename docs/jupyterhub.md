# JupyterHub on Cloudharness

Cloudharness makes available a Jupyterhub deployment 

A plain JupyterLab environment is available at the `hub.*` subdomain, but other applications can be based on 
the hub spawner to run with their own configurations and customizations.
This document provides information on how to configure jupyterhub based applications and configure them.

## Create a new JupyterHub applicaton endpoint

1. Create a new application
1. Edit the Dockerfile of your application starting from jupyter/base-notebook:hub-1.4.2
1. Edit the `deploy/values.yaml` file as following

```yaml
  subdomain: myappsubdomain
  service:
    auto: false
    port: 80
    name: proxy-public
```

## Override JupyterHub

1. Create application on `applications/jupyterhub` in your solution
1. Override any file from Cloudharness' `applications/jupyterhub`

> Note: use `-m` parameter when you run `harness-deployment` if you want to use files
> from the base Cloudharness application without copying them

## Configurations

Edit the `deploy/values.yaml` file `harness.jupyterhub` section  to edit configurations
- `args`: arguments passed to the container
- `applicationHook`: change the hook function (advances, see below)
- `extraConfig`: allows you to add Python snippets to the jupyterhub_config.py file
- `spawnerExtraConfig`: allows you to add values to the spawner object without the need of creating a new hook

Example:
```yaml
harness:
  ...
  service:
    auto: false
    port: 80
    name: proxy-public
  jupyterhub:
    args: ["--debug", "--NotebookApp.default_url=/lab"]
    extraConfig:
      timing: |
        c.Spawner.port = 8000
        c.Spawner.http_timeout = 300
        c.Spawner.start_timeout = 300
        c.JupyterHub.tornado_settings = { "headers": { "Content-Security-Policy": "frame-ancestors 'self' *.ch.local localhost"}}
    spawnerExtraConfig:
      cpu_guarantee: 0.05
      cpu_limit: 1
      mem_guarantee: 2G
      mem_limit: 4G
```

Note: The spawnerExtraConfig is a shortcut for default helm values configurations.
For instance, to define resource limites can edit `singleuser.cpu` and `singleuser.memory`:

```yaml
harness:
  ...
singleuser:
  cpu:
    limit: 0.4
    guarantee: 0.05
  memory:
    limit: 0.5G
    guarantee: 0.1G
```

Refer to the main documentation and the official [JupyterHub documentation](https://zero-to-jupyterhub.readthedocs.io/) to know about standard
configuration overridings
to the [values.yaml](../applications/jupyterhub/deploy/values.yaml) file.


## Customizing the Authenticator

Override the JupyterHub application and edit the hub/config/authenticator_class value as in the 
following example to set the cloudharness default authenticator:

```yaml
hub:
  config:
    JupyterHub:
      admin_access: true
      authenticator_class: ch
```

Main relevant authenticator classes:
- `dummy`: no authentication
- `keycloak`: ask credentials on login using the cloudharness keycloak (accounts)
- `ch`: automatically assign currently logged in users (assume the user is already logged in)


For more information about authentication and other available authenticators, 
see [here](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/authentication.html)

> Advanced: to add your custom authenticator, install it in the Dockerfile and override the file
> `deploy/resources/hub/jupyterhub_config.py` to add the authenticator.

## Customizing the Spawner (advanced)

Cloudharness provides a hook to change the pod manifest.
To add static specifications to the spawner, can edit

`harness.jupyterhub.spawnerExtraConfig` in the `deploy/values.yaml` file.

### Create the hook function 

The hook function is called before the pod is created by the KubeSpawner.
Any value in the KubeSpawner can be changed, among others:

- Add volumes/volume claims
- User assignment
- Change pod/node affinity

```python
from jupyterhub.user import User
from kubespawner.spawner import KubeSpawner

def change_pod_manifest(self: KubeSpawner):
    """
    Application Hook to change the manifest of the notebook image
    before spawning it.

    Args:
        self (KubeSpawner): the spawner

    Returns:
        -
    """
```

The hook function should be part of a library installable as a pip package.
To see a real example, refer to the main [hook implementation](../applications/jupyterhub/src/harness_jupyter/jupyterhub.py).

### Add the hook

In order to implement new hooks in your solution based on Cloudharness, you need to:
- override the jupyterhub application
- install the package with the hook function in the overridden Dockerfile
- edit values.yaml harness.jupyterhub.applicationHook

Example:
values.yaml
```yaml
harness:
  ...
  jupyterhub:
    applicationHook: "my_lib.change_pod_manifest"
    ...
```

## Customizing user environment

The `hub/jupyterhub_notebook_config.py` file runs at startup in the spawned notebook pod.
Customize the file as documented [here](https://jupyterhub.readthedocs.io/en/stable/reference/config-user-env.html).

## Change the Jupyterhub theme
Override the following files to change the theme:

- `theming/page.html`: main page template. Any layout change and css can be placed here
- `theming/spawn-pending.html`: the page shown while waiting for the pod during the spawning process

## Technical details

The deployment is adapted adapted from the official [JupyterHub helm chart](https://github.com/jupyterhub/helm-chart).
Refer to the main documentation and the official [JupyterHub documentation](https://zero-to-jupyterhub.readthedocs.io/) to know about standard
configuration overridings
to the [values.yaml](../applications/jupyterhub/deploy/values.yaml) file.

Cloudharness JupyterHub is integrated with the accounts service so enabling a shared single-sign-on with other applications in the solution.

The spawner is also adapted providing a hook to allow other applications to be based on the hub spawner to run with their own configurations.

Available