# Argo compatibility checks

Chart regressions verify the exact upstream release, CloudHarness service and
pod-naming defaults, image overrides, CRD hooks and executor RBAC:

```sh
python -m unittest discover -s applications/argo/tests -v
```

The opt-in integration test uses the CloudHarness Python API against a real
Argo server. It covers submission, listing, status, live progress, file outputs,
exit handlers after success/failure, logs, implicit image entrypoints, deletion,
script tasks and a shared-volume pipeline that retries a failed step.
It writes `1/10` and `7/10` for 75 seconds each to exercise the default reporting
interval. Allow about five minutes.

Use a disposable `kind-argo-sdk-*` cluster or a dedicated Docker Desktop test
namespace starting with `argo-`. Install the repository's models, common and CLI
packages, Helm 3, kubectl and PyYAML first. Generate and install the real
CloudHarness parent chart, so its compatibility templates are included:

```sh
export CONTEXT=kind-argo-sdk-chart-test
export NAMESPACE=argo-compatibility
# Point KUBECONFIG at this disposable cluster.
harness-deployment . -i argo -n "$NAMESPACE" -d argo.test -u -dtls -N \
  -o /tmp/argo-compatibility
helm upgrade --install "$NAMESPACE" /tmp/argo-compatibility/helm \
  --namespace "$NAMESPACE" --create-namespace --kube-context "$CONTEXT" --wait
kubectl --context "$CONTEXT" -n "$NAMESPACE" port-forward \
  service/argo-server 27461:2746 --address 127.0.0.1
```

In another terminal, with the same `KUBECONFIG`:

```sh
ARGO_SMOKE_CONTEXT=kind-argo-sdk-chart-test \
ARGO_SMOKE_NAMESPACE=argo-compatibility \
ARGO_SMOKE_URL=http://127.0.0.1:27461 \
python -m unittest discover -s applications/argo/tests \
  -p test_emissary_integration.py -v
```

The test rejects non-loopback API endpoints and other cluster contexts. It
creates and deletes its own workflows. Optional settings are `ARGO_SMOKE_IMAGE`
(default `busybox:1.37`), `ARGO_SMOKE_SERVICE_ACCOUNT` (default `argo-workflows`)
and `ARGO_SMOKE_EVIDENCE` (JSON evidence filename). The image must provide
`sh`, `echo` and `sleep`; changing it also changes the implicit-entrypoint test.
Delete the disposable cluster after collecting results.

SDK request/response regressions run without Kubernetes:

```sh
python -m pytest -q libraries/cloudharness-common/tests/test_argo_client.py
```
