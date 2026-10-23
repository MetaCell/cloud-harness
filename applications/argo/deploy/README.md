# Argo Workflows

CloudHarness uses Argo to run container workflows with the PNS executor.
Configure the vendored [Helm chart](charts/) through `argo-workflows` values;
see [values.yaml](charts/values.yaml) for options.

Tasks report progress by writing `N/M` to `ARGO_PROGRESS_FILE`.
Keep component image versions aligned and apply matching [CRDs](charts/crds/)
explicitly when upgrading; Helm does not update existing CRDs.

Run chart checks from the repository root:

```sh
helm lint applications/argo/deploy/charts
python -m pytest -q applications/argo/tests/test_components.py
```
