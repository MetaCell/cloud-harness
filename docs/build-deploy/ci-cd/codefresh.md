# Continuous deployment with Codefresh

Codefresh pipelines are generated as `deployment/codefresh-[ENV].yaml`.
These files can be loaded from codefresh as documented [here](https://codefresh.io/docs/docs/configure-ci-cd-pipeline/pipelines/).

The pipeline will take care of building the images from the source code and deploy the helm chart.
Log in to codefresh and run the pipeline associated to the repository.

- To setup a new dev pipeline, indicate the remote yaml path `./deployment/codefresh-dev.yaml`
- To setup a new production pipeline, indicate the remote yaml path `./deployment/codefresh-prod.yaml`

## Preconfigured pipelines

- [codefresh-dev.yaml](../../../deployment-configuration/codefresh-template-dev.yaml). The main CI/CD pipeline. Includes build, deployment, testing and final tagging and push. Tagging and push is made upon approval.
- [codefresh-prod.yaml](../../../deployment-configuration/codefresh-template-prod.yaml). The Production deployment pipeline. The main idea is to reuse the builds tagged in the dev pipeline with specific configurations for the production environment.
- [codefresh-stage.yaml](../../../deployment-configuration/codefresh-template-stage.yaml). The Staging deployment pipeline. The main idea is to reuse the builds tagged in the dev pipeline with specific configurations for the production environment.
- [codefresh-test.yaml](../../../deployment-configuration/codefresh-template-test.yaml). The Testing pipeline. It creates a new deployment from the current codebase and runs all tests. The deployment is deleted after the completion of the tests. See also the [testing documentation](../../testing.md).

The templates for the predefined pipeline are in the [deployment-configuration](../../../deployment-configuration) directory.

## Variables

Variables are used to customize the deployment

### General variables
- **CLOUDHARNESS_BRANCH**. Specifies the cloudharness branch or tag to use.

### Build and deploy variables
- **DOMAIN*** - The deployment's base domain
- **CLUSTER_NAME*** - The cluster context name as configured in Codefresh
- **NAMESPACE*** - The Kubernetes namespace to use
- **REGISTRY*** - The base registry address
- **CODEFRESH_REGISTRY*** - the name of the registry as configured inside Codefresh
- **REGISTRY_SECRET** - define a secret to push on the registry (not mandatory)

### Test variables

- **SKIP_TESTS** - if defined, skips all tests

### Releasing variables

- **REGISTRY_PUBLISH_URL**. The base url of the registry to push to publish
- **DEPLOYMENT_PUBLISH_TAG**. The tag in which to publish
- **DEPLOYMENT_TAG**. Required for stage and prod pipelines, specifies the tag from a previous publish step. For instance, if the dev pipeline had `DEPLOYMENT_PUBLISH_TAG=1.0` then we need to set `DEPLOYMENT_TAG=1.0` in the stage and production steps.

### Automatic variables

- Codefresh variables. All variables starting with `CF_` are managed by codefresh
- **[APPNAME]_TAG**. This set of variables are created in the `prepare_deployment` step. The tag is derived from an hash of the content being built.
- **[APPNAME]_TAG_EXISTS**. This set of variables are created in the `prepare_deployment` step. If a manifest for `[APPNAME]_TAG` exists, `[APPNAME]_TAG_EXISTS` is set. This is used to implement smart caching

### Cache variables
**[APPNAME]_FORCE_BUILD**. Set it to force the build of the build of the image named `[APPNAME]_TAG`

## Update a deployment specification

The deployment must be updated whenever new build artifacts are added/removed, or opon changes in the templates.

To update a pipeline for a specific env, run
```
harness-deployment . -e [ENV]
```

A file `./deployment/codefresh-dev.yaml` is created, provided that a file `./deployment/codefresh-[ENV].yaml` exists either as a preconfigured pipeline on cloudharness or as a custom pipeline in your application.

## Override Codefresh pipeline templates
Edit `./deployment-configuration/codefresh-template-[ENV].yaml` to override any helm chart values file.
Notice that Codefresh templates will be generated only if a specific environment file is defined.
By default, the *dev* and *prod* environments are defined.

To override the single image build template, edit  `deployment-configuration/codefresh-build-template.yaml`



## Create and override the pipelines

Create a file named `./deployment-configuration/codefresh-template-[ENV].yaml` to create a specific
pipeline. The file can include any additional step in addition to the predefined ones.

If [ENV] is one of `dev`, `stage`, `prod`, `test`, you only need to specify the additional steps you want to add, or change the bit in the file you need to change.

## Caching and conditional build

The dev and test pipelines use content hash to avoid doing the same build twice.
The `.dockerignore` file is used to determine the content which is part of the hashing.

Caching may be problematic if the build is relying on data which is not in the repo which has to be updated.
In this case, set the `[APPNAME]_FORCE_BUILD` variable to force a new build.