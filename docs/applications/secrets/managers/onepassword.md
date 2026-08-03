# Secret manager: `onepassword`

Reads application secrets from 1Password, through the
[1Password Kubernetes Operator](https://developer.1password.com/docs/k8s/k8s-operator/).

CloudHarness renders one `OnePasswordItem` custom resource per secret. The operator is what
authenticates to 1Password, fetches the item and materializes the Kubernetes Secret that
CloudHarness then mounts with the other secrets of the application.

## Cluster setup

The operator reaches 1Password in one of two ways, and only one of them is needed. Both are
documented in the [operator usage guide](https://github.com/1Password/onepassword-operator/blob/main/USAGEGUIDE.md).

### Option 1 — Connect server (recommended for a shared cluster)

1Password Connect runs in the cluster and holds the credentials; the operator talks to it.
The [Helm chart](https://github.com/1Password/connect-helm-charts) installs both at once.

1. Create a
   [Connect server and credentials file](https://developer.1password.com/docs/connect/get-started/)
   in your 1Password account. You end up with a `1password-credentials.json` file and a
   Connect token.

2. Install Connect together with the operator:

   ```bash
   helm repo add 1password https://1password.github.io/connect-helm-charts
   helm install connect 1password/connect \
     --set-file connect.credentials=1password-credentials.json \
     --set operator.create=true \
     --set operator.token.value=<your connect token>
   ```

### Option 2 — Service account

The operator authenticates directly with a
[1Password service account](https://developer.1password.com/docs/service-accounts) token,
with no Connect server to run.

1. [Create a service account](https://developer.1password.com/docs/service-accounts/get-started#create-a-service-account)
   and grant it read access to the vault holding the secrets.

2. Store its token in the cluster:

   ```bash
   kubectl create secret generic onepassword-service-account-token \
     --from-literal=token="$OP_SERVICE_ACCOUNT_TOKEN"
   ```

3. Deploy the operator with `OP_SERVICE_ACCOUNT_TOKEN` set from that secret, and without
   `OP_CONNECT_TOKEN` / `OP_CONNECT_HOST`.

### Operator settings worth knowing

| Variable | Default | Why it matters here |
| --- | --- | --- |
| `WATCH_NAMESPACE` | all namespaces | Must cover the namespace CloudHarness deploys to, otherwise the `OnePasswordItem` resources are ignored and the secrets never appear. |
| `POLLING_INTERVAL` | `600` (seconds) | How long a change in 1Password takes to reach the cluster. CloudHarness mounts secrets as files, which the kubelet refreshes in place, so a change propagates without restarting anything. |
| `AUTO_RESTART` | `false` | Leave it off unless an application caches secrets at startup: mounted files update on their own. |

## Configuration

### Per secret

```yaml
harness:
  secrets:
    mySecret:
      manager: onepassword
      path: vaults/my-vault/items/my-item
      field: password
```

| Setting | Required | Default | Meaning |
| --- | --- | --- | --- |
| `path` | yes | — | Path of the 1Password item, `vaults/<vault>/items/<item>`. Both parts accept an id or a title. The item name can be given alone when `secretmanagers.onepassword.vault` is set. |
| `field` | no | `password` | Field of the item holding the value. The operator turns every field of the item into a key of the Kubernetes Secret; this picks the one to expose. |
| `apiVersion` | no | `onepassword.com/v1` | For a cluster running a different version of the operator's CRD. |
| `default` | no | — | Value used for local docker compose deployments, where no operator exists. |

### Deployment wide

```yaml
secretmanagers:
  onepassword:
    vault: my-vault
```

| Setting | Default | Meaning |
| --- | --- | --- |
| `vault` | — | Default vault, so secrets can name their item alone instead of repeating the full path. |
| `apiVersion` | `onepassword.com/v1` | Applied to every `onepassword` secret. |

This section holds no credentials — the operator has its own — and it is exposed in the
`cloudharness-allvalues` config map, so never put a token in it.

## What gets rendered

For a secret `mySecret` of an application deployed as `myapp`:

```yaml
apiVersion: onepassword.com/v1
kind: OnePasswordItem
metadata:
  name: myapp-mysecret
  namespace: <namespace>
  labels:
    app: myapp
spec:
  itemPath: "vaults/my-vault/items/my-item"
```

The operator creates a Kubernetes Secret named `myapp-mysecret` holding every field of the
1Password item. CloudHarness projects only `field` from it into
`/opt/cloudharness/resources/secrets/myapp/mySecret`, so the application reads it with
`get_secret("mySecret")` like any other secret.

## Gotchas

* **Field names are normalized.** The operator lowercases field names, strips invalid
  leading and trailing characters and replaces inner whitespace with `-`, so a 1Password
  field named `API Token` becomes the key `api-token`. `field` must match the normalized
  form, not what you see in the 1Password UI.
* **Titles are ambiguous.** When several vaults or items share a title, the operator picks
  the oldest one. Use ids in `path` when that is a risk.
* **File fields.** A field storing a file contributes the file contents as the value. If a
  file field and another field share a name, the non-file one wins.
* **Freezing a value.** Adding the tag `operator.1password.io:ignore-secret` to the item in
  1Password stops the operator from propagating further updates.
* **Moving an existing secret to this manager.** Delete the old entry from the application
  secret (`kubectl edit secret myapp`) as part of the upgrade, otherwise the same file is
  claimed twice and the pod fails to mount its secrets directory.

## References

* [1Password Kubernetes Operator](https://developer.1password.com/docs/k8s/k8s-operator/)
* [Operator usage guide](https://github.com/1Password/onepassword-operator/blob/main/USAGEGUIDE.md)
* [Connect Helm charts](https://github.com/1Password/connect-helm-charts)
* [1Password Connect](https://developer.1password.com/docs/connect/)
* [1Password service accounts](https://developer.1password.com/docs/service-accounts)
* Implementation: `deployment-configuration/helm/templates/secrets/managers/onepassword.tpl`
