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
the same stages as the Codefresh pipeline: image build, unit tests, helm deployment, rollout wait, API/E2E tests
and publication. Pass `-ci codefresh -ci github` to generate both. Build, unit tests and deployment run with
[Skaffold](https://skaffold.dev/), from the `deployment/skaffold-ci.yaml` the pipeline writes.

- Build: the `prepare` job runs `harness-deployment --write-env --write-skaffold-ci`, which asks the
  registry for every image's content-hash tag and writes `deployment/skaffold-ci.yaml` with only the images
  whose tag is missing (or forced). The same job then runs `skaffold build` on it: every image is a
  `docker buildx build --push` with its registry cache (`[image]:buildcache`), skaffold runs them in parallel and
  builds a base image before the images built on it, while base images that are already published are pulled.
  The more CPUs the build runner has, the more images build at once. `skaffold test` then runs the unit tests of
  every app (the `test` section of the same file) against every image of the deployment, rebuilt or not
  (`deployment/skaffold-images.json`). A re-run after a failure asks the registry again, only builds what is
  still missing and tests everything again. The steps live under `cloudharness.build` in the template (`null`
  in stage and prod, which deploy published images).
- Deployment: the `deploy` job runs `skaffold deploy` on the same file, which installs or upgrades the helm
  chart (release and namespace named after the deployment namespace) and waits until its deployments and
  statefulsets are rolled out, tolerating restarts for up to 15 minutes. Skaffold labels every pod template
  with its run id: the workflow sets a constant one, so the apps whose image did not change are not restarted.
  Secret values reach helm with `--set-file`, from files the job writes under `~/.cloudharness/secrets`.
- Templates: `deployment-configuration/github-template.yaml` (job prototypes and shared steps) plus
  `github-template-[dev|stage|prod|test].yaml` (name, triggers, per-environment deltas), layered and overridable
  from your project's `deployment-configuration/` like the Codefresh ones. A `jobs.tests-api-[app]` or
  `jobs.tests-e2e-[app]` entry in your template is merged over that app's generated job.
- Runner: set the `CH_GITHUB_RUNNER` repository or organization variable to the runner label (for ARC, the
  runner scale set name); `prepare`, which builds the images, reads `CH_GITHUB_BUILD_RUNNER` first, so images can
  build on a bigger runner. Both are read when the workflow runs, so changing runners needs no regeneration. When neither is
  set, jobs use the runner given at generation time by the `CH_GITHUB_RUNNER` environment variable (default
  `ubuntu-latest`, comma-separated labels allowed). A `runs-on` in the template always wins.
- Configuration: the generator logs the repository variables (`REGISTRY`, `DOMAIN`, `NAMESPACE`, ...) and
  secrets (`REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `KUBECONFIG`, the application secrets with the same names
  as the Codefresh variables) the workflow expects. Approvals are GitHub environment protection rules on the
  `publish` and `prod`/`stage` environments. `workflow_dispatch` inputs replace the `DEPLOYMENT_PUBLISH_TAG`,
  `DEPLOYMENT_TAG`, `*_TAG_FORCE_BUILD` and `SKIP_TESTS` pipeline variables. A project's jobs clone and install
  the cloud-harness branch named by the `CLOUDHARNESS_BRANCH` variable (default `develop`); cloud-harness' own
  workflow builds and tests the branch that triggered it, tools included, and does not read that variable.
- Cluster credentials: the `deploy` and test `cleanup` jobs run the steps listed under
  `cloudharness.kube_auth` in the template. The default step uses a base64 `KUBECONFIG` secret when present and
  the runner's own cluster access otherwise (a runner inside the target cluster with a service account bound to
  the deployment namespaces needs no secret at all); with neither, the job fails immediately. Only `deploy`
  targets the GitHub environment named after the CloudHarness environment (so required reviewers on
  `stage`/`prod` approve the deployment once): `cleanup` reads repository or organization secrets, which an
  environment secret of the same name overrides for `deploy`. For GKE with workload identity
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
    cleanup:
      permissions: {contents: read, packages: write, id-token: write}
  ```
- Test failures: unit tests gate the deployment, as in Codefresh. The API/E2E tests run after the deployment
  and never block it, but `publish` (and `git-tag` on stage) is skipped when anything failed. To publish
  despite failing tests, as Codefresh's `fail_fast: false` does, override the `if` of `publish` in your
  project's template and protect the `publish` environment with required reviewers.
