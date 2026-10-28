# Argo Workflows

CloudHarness vendors the unmodified official [ArgoProj Helm chart 2.0.14](https://github.com/argoproj/argo-helm/releases/tag/argo-workflows-2.0.14),
which deploys Argo Workflows **v4.1.6** with the Emissary executor.
The Python client is pinned separately to `argo-workflows==6.7.18`.

CloudHarness integration lives outside the upstream chart: the `argo-server`
Service address, `argo-workflows` workflow service account, namespace scope,
server authentication mode and `POD_NAMES=v1` naming defaults are retained.
Explicit `controller.extraEnv` and `server.extraEnv` settings take precedence
over the naming default. The controller retains Secret `get` access for image
entrypoint discovery; existing CloudHarness service-account bindings are unchanged.

## Deployment

Use the normal CloudHarness generation and Helm deployment flow. The upstream
chart's pre-install/pre-upgrade hook installs and updates the full CRDs; a separate
`kubectl apply` is unnecessary with the default settings. Keep the hook enabled
unless CRDs are managed separately. Helm rendering alone does not execute hooks.

Let active PNS workflows finish before switching to Emissary. Remove obsolete
executor settings and old component image pins from consuming deployment values,
or update controller, server and executor together. Image overrides remain
available under `argo-workflows.controller.image`, `server.image` and
`executor.image`.

## Tasks and progress

Existing CloudHarness operations and tasks continue to use the Argo REST API.
Emissary runs the task command inside its main container; when `command` is
omitted, Argo resolves the image entrypoint. Private registry credentials must be
available through workflow or service-account image-pull Secrets.

Self-reported progress is optional. To use it, write a `completed/total` ratio,
for example `echo 3/10 > "$ARGO_PROGRESS_FILE"`, from the task.
Argo reads the file approximately every three seconds and normally reports
updates once a minute. The standard Workflow API exposes the result in
`status.nodes[...].progress`; polling and reconciliation can add latency.

See [compatibility checks](../tests/README.md) for the regression and isolated
Kubernetes tests, and the upstream [upgrade notes](https://argo-workflows.readthedocs.io/en/latest/upgrading/).
