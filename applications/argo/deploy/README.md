# Argo Workflows components

CloudHarness vendors the Argo chart here. This revision upgrades the controller,
server, executor and eight official minimal CRDs from 3.1.15 to **3.7.18**.
The Python dependency remains argo-workflows==5.0.0. Workflow submission methods,
operation/status/log endpoints and response shapes are unchanged.

## Compatibility

- Argo 3.7 uses Emissary. Removed PNS/runtime-selection fields and pod-worker
  arguments are no longer rendered. Old executor-selection values are ignored.
- Controller and server both retain POD_NAMES=v1. The existing CloudHarness log
  helper resolves pod names from node IDs, so changing this convention would
  break its behavior.
- The server uses ARGO_BASE_HREF. Service names and auth-mode configuration remain.
- Component roles and workflow executor roles include WorkflowTaskResult access,
  which supports native progress and task completion.
- CloudHarness still accepts integer TTL seconds and integer pod-GC delay values.
  Its internal serializer copies those settings and emits the Argo duration as,
  for example, "86400s". It preserves strings and does not mutate caller inputs.
  No new progress API fields, request fields, listener or SDK migration is added.
- The existing get_workflow helper still raises on failed workflows. This
  behavior is deliberately unchanged.

## Upgrade existing installations

Helm installs files in crds/ initially but does not upgrade existing CRDs.
Finish active workflows before upgrading. **First rebuild and deploy the
workflow-submitting application images with the duration-serialization fix in
this PR.** Updating the Argo server alone does not update libraries inside
existing application images; their old numeric delay payloads would receive
HTTP 400. Public caller inputs stay the same, but the fixed library must be
present in those images. Then apply the vendored CRDs explicitly
using the intended context, then deploy the chart through the existing
CloudHarness deployment process:

    kubectl --context <context> apply --server-side --field-manager=cloud-harness-argo-upgrade --force-conflicts -f applications/argo/deploy/charts/crds

The force-conflicts flag replaces the old Helm-owned schema version fields.
Review this command for the chosen installation; no remote rollout is part of
the local NeuroGlass validation. Old deployment overrides pinning Argo image
tags must also be updated for controller, server and executor together.

These CRDs are extracted without semantic changes from the official
https://github.com/argoproj/argo-workflows/releases/download/v3.7.18/install.yaml
SHA-256: bd0871baab5265f02dc61130c408300385e87183263fd87036786ed5fc751a4a.

## Progress

A workflow process can write completed/total into ARGO_PROGRESS_FILE. Argo stores
the observation in the processing node's status.progress. Consumers can read it
through the existing Argo SDK; the CloudHarness API contract is unchanged.

By default the executor reads every three seconds and publishes approximately
once a minute. For local acceptance tests only, controller.extraEnv sets
ARGO_PROGRESS_PATCH_TICK_DURATION=3s and ARGO_PROGRESS_FILE_TICK_DURATION=1s.
These variables belong on the controller: it supplies them to workflow pods.
No faster interval is imposed on production deployments by this change.

## Local checks

    helm lint applications/argo/deploy/charts
    python -m pytest -q applications/argo/tests/test_components.py
    python -m pytest -q libraries/cloudharness-common/tests/test_on_exit_notify.py libraries/cloudharness-common/tests/test_pod_gc.py

The rendered-component tests require Helm and PyYAML. Backend contract tests use
the existing CloudHarness test environment. Neither requires a cluster.
Combined with the independent custom exit-handler command in CloudHarness PR #879,
the companion MNP PR #1452 documents the local Docker Desktop integration:
native two-batch phase progress, successful/failed finite workflows, exit
handlers, existing SDK submission and log retrieval. Microtask creation remains
a separate feature.
