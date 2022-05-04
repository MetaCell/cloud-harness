# Cloudharness workflows
Cloudharness allows to run workflows through [Argo workflows](https://github.com/argoproj/argo-workflows) providing the Argo installation and a Python library to run workflows programmatically.

## Access the Argo ui

The Argo-ui is available on the `argo` subdomain in your deployment. Can use the Argo-ui to monitor and inspect workflows.
By default the ui is protected by a gatekeeper, so an admin user credentials are needed to use the application. To disable the gatekeepers use the parameter `-u` when running `harness-deployment`.

## The Workflows micro service

The workflow micro service application defines some common use cases tasks and a REST api to monitor workflows.
It is accessible at the address workflows.MYDOMAIN when it is included in the deployment.

## Define Workflows custom Tasks

Tasks can be created below an application is the `tasks` directory.
Every Dockerfile below the `tasks` subdirectory is recognized as an image to build aside the containing application.

For instance, given this folder structure:

```
applications
  myapp
    tasks
      t1
        Dockerfile
      t2
        Dockerfile
```

The two artifacts `myapp-t1` and `myapp-t2` are built and available to be used as custom tasks inside workflow.

## Run workflows

See the [Python api](./applications/development/workflows-api.md) to know how to create and run a workflow.


