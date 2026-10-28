# Argo Workflows

CloudHarness uses Argo 3.3.10 with the PNS executor. Configure the vendored
[Helm chart](charts/) through `argo-workflows` values; see
[values.yaml](charts/values.yaml) for options.

## Controller progress fix

The Argo application image builds the official 3.3.10 controller at commit
`b19870d737a14b21d86f6267642a63dd14e5acd5` with a small
[TaskResult event-handler backport](../controller/taskresult.patch) from
[upstream Argo 3.5.8](https://github.com/argoproj/argo-workflows/blob/v3.5.8/workflow/controller/taskresult.go).
It reports version `v3.3.10-ch.1`. The server, executor and seven CRDs remain
the official 3.3.10 release. PNS, pod names, workflow outputs, logs and the
CloudHarness SDK/API contract are unchanged.

Unmodified 3.3.10 receives TaskResults but does not enqueue a Workflow when
they change. A long-running task can therefore show stale Workflow progress
until another event or the roughly twenty-minute reconciliation. Relying on
pod-annotation fallback does not fix normal CloudHarness deployments: the
workflow service account can already create TaskResults through its broader
permissions.

The backport queues the owning Workflow on TaskResult creation/update through
Argo's existing rate-limited work queue. It adds no polling process or
application-specific progress reader. The executor Role grants native
TaskResult create/patch permissions; existing permissions are preserved.

CloudHarness builds `applications/argo/Dockerfile` through its ordinary
application-image pipeline. The parent Helm wrapper renders the existing
controller template with that image and the configured registry pull Secret;
it does not create an extra application Deployment. Explicit
`argo-workflows.controller.image` overrides remain available, but replacing the
built controller with an unpatched upstream image also removes this fix.
The vendored chart can still render standalone with its explicit controller
image settings.

## Self-reported progress

Tasks overwrite `ARGO_PROGRESS_FILE` with one `completed/total` ratio.
By default the executor reads it every three seconds and publishes changed
progress to a WorkflowTaskResult approximately once per minute. The patched
controller then reconciles the Workflow through its normal work queue
(default delay ten seconds). Consumers read ordinary Workflow status through
the existing CloudHarness workflow API. Scheduling, API load and application
caching can add delay; these intervals are not a maximum-latency guarantee.

For a task reporting `2/4`, inspect the Workflow while its pod is still running
and confirm that the processing node's `progress` becomes `2/4`. Waiting only
for pod completion would miss the original propagation regression.

## Validation and upgrades

Keep component versions aligned and apply matching [CRDs](charts/crds/)
explicitly when upgrading; Helm does not update existing CRDs.

Run chart checks from the repository root:

```sh
helm lint applications/argo/deploy/charts
python -m pytest -q applications/argo/tests/test_components.py
docker build -t cloudharness-argo-progress-test applications/argo
```

Building the Argo image also runs a Go regression test against the real
TaskResult informer/watch and work queue. It covers both TaskResult creation
and multiple progress updates, without waiting for pod completion.
