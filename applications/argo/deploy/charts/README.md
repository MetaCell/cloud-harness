# Argo Workflows chart

CloudHarness vendors this chart and uses official Argo Workflows **v4.1.6**
images with the Emissary executor. See the [deployment and upgrade guide](../README.md)
for CRD updates, migration from PNS and compatibility checks.

`values.yaml` configures the controller, server, executor, service accounts and
RBAC. Image overrides remain under `controller.image`, `server.image` and
`executor.image`. Keep all component versions aligned.

By default, `singleNamespace: true` limits the controller and server to their
release namespace. Set `singleNamespace: false` only when cluster-scoped workflow
management is required. `controller.instanceID` can further select participating
workflows when multiple controllers share that scope.

The eight files in `crds/` are generated official minimal CRDs from Argo v4.1.6.
Helm installs them for a new release but does not upgrade existing CRDs; apply
the matching files separately before rolling out new component images.
