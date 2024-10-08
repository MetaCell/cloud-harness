# CI/CD with CloudHarness

CloudHarness supports continuous deployment natively by creating the Helm Chart for you and with a few 
ways to build containers.

## CI/CD with Skaffold

[Skaffold](https://skaffold.dev/) is a command line tool that simplifies build and deployment  on a Kubernetes cluster. The configuration as `skaffold.yaml` file is created when running
`harness-deployment`.

All you need to to is:
- Configure the Kubernetes cluster in your local shell (e.g. `gcloud init` on Google Cloud)
- Configure the local Docker to be able to push to the remote registry
- Create the deployment specifying the registry and remote domain -- `harness-deployment ... -r myregistry -d mydomain`
- Run `skaffold build`
- Run `skaffold run`

### Dockerfile configuration with Skaffold

When defining an applications values you can provide details on dockerfile configuration such as build arguments. This feature is intended to support useful development use cases (e.g. conditionally running unit tests via build arguments) and should be used with caution as it can lead to different images in different deployment environments.

## CI/CD with Codefresh

[Codefresh](https://codefresh.io/) is a nice platform for CI/CD see details in the [dedicated document](./codefresh.md).