# Argo Workflows

CloudHarness uses the official **Argo Workflows v4.1.6** controller, server and
executor images. **Emissary** is Argo's executor; PNS is no longer supported.
There is no CloudHarness controller image, source patch or image build.

The CloudHarness workflow API is unchanged. The Python client is pinned to
`argo-workflows==6.7.18`; SDK and Argo runtime versions have separate numbering.
Existing operations, tasks, submission, status and log methods continue to use
the Argo REST API. `POD_NAMES=v1` preserves the pod names used by CloudHarness log lookup;
explicit `controller.extraEnv` and `server.extraEnv` settings still take precedence.
The internal pod-GC delay is serialized as a duration (`86400s`) rather than an
integer; callers continue to supply TTL values in seconds.

## Upgrading an existing installation

1. Let existing workflows finish, or explicitly stop them and retain their data.
   Do not switch an active PNS workflow to Emissary in place.
2. Apply the CRDs from `charts/crds` **before** rolling out the components. They
   are the eight official minimal CRDs from tag `v4.1.6`, commit
   `43021573c5a35cbafae009043c132dfcef43a112`. Helm installs CRDs on a fresh
   installation but does not update existing ones:

   ```sh
   kubectl --context "$CONTEXT" apply --server-side \
     -f applications/argo/deploy/charts/crds/
   ```

   Review any server-side ownership conflicts before transferring ownership.
   Minimal CRDs retain Argo's validation of Workflow specs in the server/controller;
   the generated files should be refreshed from the same release when upgrading.
3. Remove old component image pins from consuming deployment values, or update
   **all three** image tags to `v4.1.6`. Remove `containerRuntimeExecutor`,
   `containerRuntimeExecutors` and obsolete executor-selection labels. The chart
   no longer emits these settings or the removed `--pod-workers` flag.
4. Deploy through the normal CloudHarness Helm generation and deployment flow.
   Image registry/repository/tag overrides remain available in
   `controller.image`, `server.image` and `executor.image`.
5. Check controller/server readiness, then exercise a finite workflow, output
   parameter, exit handler and live progress before resuming ingestion.

The controller Role includes current task-result, task-set and artifact-GC
resources. The chart's workflow service account receives `create` and `patch`
for `workflowtaskresults`; supply the same permissions when using a different
workflow service account. Existing CloudHarness service-account bindings are
unchanged by this upgrade.

## Execution and progress

Emissary wraps the task command inside its main container and uses init/wait
containers to collect results. Existing explicit task commands work unchanged.
For tasks that omit `command`, Argo resolves the image entrypoint; private
registries must remain reachable and their image-pull Secrets available. Output
parameters can still be read from a file in the task container's filesystem.

Tasks publish native progress by writing a `completed/total` ratio into
`ARGO_PROGRESS_FILE`. Argo's executor defaults to reading that file every three
seconds and reporting approximately once a minute. In v4.1.6, TaskResult updates
natively enqueue their Workflow for reconciliation; no patched controller or
application-side TaskResult reader is needed. Reconciliation and API caching
still add latency, so this is not a hard one-minute delivery guarantee.

## Validation

Run chart regressions with Helm 3 and PyYAML installed:

```sh
python -m unittest discover -s applications/argo/tests -v
```

See `applications/argo/tests/README.md` for the optional isolated Kubernetes
compatibility test. Deployment values in an application repository can override
these defaults; upgrading CloudHarness alone does not remove those overrides.

Upstream references:

- [v4.1.6 release](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.6)
- [Upgrade notes](https://argo-workflows.readthedocs.io/en/latest/upgrading/)
- [Workflow executors](https://argo-workflows.readthedocs.io/en/latest/workflow-executors/)
