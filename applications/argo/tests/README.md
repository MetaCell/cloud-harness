# Argo compatibility checks

The chart tests run without a cluster and cover official component versions,
removed executor settings, legacy pod naming, image overrides, CRDs and executor
RBAC. CI runs them alongside the existing CloudHarness library and CLI tests.

```sh
python -m unittest discover -s applications/argo/tests -v
```

The optional `test_emissary_integration.py` exercises the existing CloudHarness
Python client against a real Argo API. It verifies submission, listing, status,
live Workflow progress, a file-backed output parameter, exit handlers after
success/failure, log lookup, implicit image entrypoint resolution and deletion.
It writes `1/10` and `7/10` for 75 seconds each, so the test exercises the default
one-minute reporting interval without executor tuning. Allow about five minutes.

This test is restricted to `docker-desktop`, a loopback API endpoint and a
namespace starting with `argo-`. It creates and deletes only its own workflows;
use a dedicated test namespace. Install the repository's models/common packages,
PyYAML and Helm 3 before running it.

```sh
CONTEXT=docker-desktop
NAMESPACE=argo-compatibility
CHART=applications/argo/deploy/charts

kubectl --context "$CONTEXT" create namespace "$NAMESPACE"
kubectl --context "$CONTEXT" apply --server-side -f "$CHART/crds/"
helm template compatibility "$CHART" --namespace "$NAMESPACE" \
  --set createAggregateRoles=false \
  --set controller.clusterWorkflowTemplates.enabled=false \
  --set server.clusterWorkflowTemplates.enabled=false \
  --set workflow.serviceAccount.create=true \
  --set workflow.serviceAccount.name=emissary-executor \
  | kubectl --context "$CONTEXT" -n "$NAMESPACE" apply -f -
kubectl --context "$CONTEXT" -n "$NAMESPACE" create configmap \
  cloudharness-allvalues --from-literal='allvalues.yaml={}'
kubectl --context "$CONTEXT" -n "$NAMESPACE" port-forward \
  service/argo-server 27461:2746 --address 127.0.0.1
```

In another terminal:

```sh
ARGO_SMOKE_URL=http://127.0.0.1:27461 \
ARGO_SMOKE_NAMESPACE=argo-compatibility \
python -m unittest discover -s applications/argo/tests \
  -p test_emissary_integration.py -v
```

Optional settings are `ARGO_SMOKE_IMAGE` (defaults to `busybox:1.37`),
`ARGO_SMOKE_SERVICE_ACCOUNT` (defaults to `emissary-executor`) and
`ARGO_SMOKE_EVIDENCE` (a JSON output filename for observed progress and terminal
statuses). The chosen image must provide `sh`, `echo` and `sleep`; changing it
also changes the implicit-entrypoint test.

After collecting diagnostics, delete the dedicated test namespace. Keep the
matching CRDs when another local Argo installation still needs them.
