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

## CI/CD with GitHub Actions

`harness-deployment -ci github -e [ENV]` generates `.github/workflows/cloudharness-[ENV].yaml`, a workflow with
the same stages as the Codefresh pipeline: one build job per image (skipped when the image's content-hash tag
already exists in the registry), unit tests, helm deployment, rollout wait, API/E2E tests and publication.
Pass `-ci codefresh -ci github` to generate both.

- Templates: `deployment-configuration/github-template.yaml` (job prototypes and shared steps) plus
  `github-template-[dev|stage|prod|test].yaml` (name, triggers, per-environment deltas), layered and overridable
  from your project's `deployment-configuration/` like the Codefresh ones. A `jobs.build-[image]` entry in your
  template is merged over that image's generated job (for instance to pick a bigger runner).
- Runner: the `CH_GITHUB_RUNNER` environment variable at generation time (default `ubuntu-latest`,
  comma-separated labels allowed); any job can still set its own `runs-on` in the template.
- Configuration: the generator logs the repository variables (`REGISTRY`, `DOMAIN`, `NAMESPACE`, ...) and
  secrets (`REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `KUBECONFIG`, the application secrets with the same names
  as the Codefresh variables) the workflow expects. Approvals are GitHub environment protection rules on the
  `publish` and `prod`/`stage` environments. `workflow_dispatch` inputs replace the `DEPLOYMENT_PUBLISH_TAG`,
  `DEPLOYMENT_TAG`, `*_TAG_FORCE_BUILD` and `SKIP_TESTS` pipeline variables.
