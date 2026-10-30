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
- Runner: set the `CH_GITHUB_RUNNER` repository or organization variable to the runner label (for ARC, the
  runner scale set name); build jobs read `CH_GITHUB_BUILD_RUNNER` first, so images can build on bigger
  runners. Both are read when the workflow runs, so changing runners needs no regeneration. When neither is
  set, jobs use the runner given at generation time by the `CH_GITHUB_RUNNER` environment variable (default
  `ubuntu-latest`, comma-separated labels allowed). A `runs-on` in the template always wins.
- Configuration: the generator logs the repository variables (`REGISTRY`, `DOMAIN`, `NAMESPACE`, ...) and
  secrets (`REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `KUBECONFIG`, the application secrets with the same names
  as the Codefresh variables) the workflow expects. Approvals are GitHub environment protection rules on the
  `publish` and `prod`/`stage` environments. `workflow_dispatch` inputs replace the `DEPLOYMENT_PUBLISH_TAG`,
  `DEPLOYMENT_TAG`, `*_TAG_FORCE_BUILD` and `SKIP_TESTS` pipeline variables.
- Cluster credentials: the `deploy`, `wait-deployment` and test `cleanup` jobs run the steps listed under
  `cloudharness.kube_auth` in the template. The default step uses a base64 `KUBECONFIG` secret when present and
  the runner's own cluster access otherwise (a runner inside the target cluster with a service account bound to
  the deployment namespaces needs no secret at all); with neither, the job fails immediately. Only `deploy`
  targets the GitHub environment named after the CloudHarness environment (so required reviewers on
  `stage`/`prod` approve the deployment once): `wait-deployment` and `cleanup` read repository or organization
  secrets, which an environment secret of the same name overrides for `deploy`. For GKE with workload identity
  federation, replace the list in your project's `github-template.yaml` and grant `id-token: write` to the jobs
  using it (it is not granted to the whole workflow; a job-level `permissions` replaces the workflow-level one):

  ```yaml
  cloudharness:
    kube_auth:
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ vars.GCP_DEPLOY_SERVICE_ACCOUNT }}
      - uses: google-github-actions/get-gke-credentials@v2
        with:
          cluster_name: ${{ vars.GKE_CLUSTER }}
          location: ${{ vars.GKE_LOCATION }}
  jobs:
    deploy:
      permissions: {contents: read, packages: write, id-token: write}
    wait-deployment:
      permissions: {contents: read, packages: write, id-token: write}
  ```
- Test failures: unit tests gate the deployment, as in Codefresh. The API/E2E tests run after the deployment
  and never block it, but `publish` (and `git-tag` on stage) is skipped when anything failed. To publish
  despite failing tests, as Codefresh's `fail_fast: false` does, override the `if` of `publish` in your
  project's template and protect the `publish` environment with required reviewers.
