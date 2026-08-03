# Secret manager: `aws`

Reads application secrets from AWS Secrets Manager, through the
[External Secrets Operator](https://external-secrets.io/) (ESO).

CloudHarness renders one `ExternalSecret` custom resource per secret. The operator is what
authenticates to AWS, reads the value and materializes the Kubernetes Secret that
CloudHarness then mounts with the other secrets of the application.

## Cluster setup

### 1. Install the operator

```bash
helm repo add external-secrets https://charts.external-secrets.io

helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace
```

See the [getting started guide](https://external-secrets.io/latest/introduction/getting-started/).
The chart installs the CRDs by default; pass `--set installCRDs=false` if you manage them
separately, in which case they must be applied with server-side apply as they exceed the
256KB annotation limit.

### 2. Grant access to the secrets

Attach an IAM policy scoped to the secrets the cluster may read, rather than all of them:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      "Resource": [
        "arn:aws:secretsmanager:eu-west-1:123456789012:secret:myproject-*"
      ]
    }
  ]
}
```

### 3. Create the store

A store says which AWS account and region to read from, and how to authenticate. Use a
`ClusterSecretStore` when several namespaces share it, a `SecretStore` when it belongs to
one namespace. With static credentials:

```bash
echo -n 'KEYID' > ./access-key
echo -n 'SECRETKEY' > ./secret-access-key
kubectl create secret generic awssm-secret \
  --from-file=./access-key --from-file=./secret-access-key
```

```yaml
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-west-1
      # optional, to assume a role scoped to the secrets above
      role: arn:aws:iam::123456789012:role/external-secrets
      auth:
        secretRef:
          accessKeyIDSecretRef:
            name: awssm-secret
            key: access-key
            namespace: external-secrets
          secretAccessKeySecretRef:
            name: awssm-secret
            key: secret-access-key
            namespace: external-secrets
```

On EKS, prefer
[IRSA or the pod identity](https://external-secrets.io/latest/provider/aws-secrets-manager/)
over static keys and drop the `auth` block entirely.

For a `ClusterSecretStore` the `namespace` of each secret reference is required, as the
store is not itself namespaced.

### 4. Point CloudHarness at it

```yaml
secretmanagers:
  aws:
    store: aws-secrets-manager
```

## Configuration

### Per secret

```yaml
harness:
  secrets:
    mySecret:
      manager: aws
      arn: arn:aws:secretsmanager:eu-west-1:123456789012:secret:my-secret
      property: password
```

| Setting | Required | Default | Meaning |
| --- | --- | --- | --- |
| `arn` | yes | — | ARN, or plain name, of the secret in AWS Secrets Manager. Becomes the operator's `remoteRef.key`. |
| `property` | no | — | Key to extract when the AWS secret holds a JSON document. Without it the whole remote value is used. |
| `store` | no | from `secretmanagers.aws` | Overrides the deployment wide store for this one secret. |
| `default` | no | — | Value used for local docker compose deployments, where no operator exists. |

### Deployment wide

```yaml
secretmanagers:
  aws:
    store: aws-secrets-manager
    storeKind: ClusterSecretStore
    refreshInterval: 1h
```

| Setting | Required | Default | Meaning |
| --- | --- | --- | --- |
| `store` | yes | — | Name of the store to read from. Shared by the deployment, which is why it lives here rather than on each secret. |
| `storeKind` | no | `ClusterSecretStore` | Set to `SecretStore` for a store defined in the release namespace. |
| `refreshInterval` | no | `1h` | How often the operator re-reads AWS. CloudHarness mounts secrets as files, so a refreshed value reaches the application without a restart. |
| `apiVersion` | no | `external-secrets.io/v1beta1` | See the version note below. |

This section holds no credentials — the store does — and it is exposed in the
`cloudharness-allvalues` config map, so never put an access key in it.

## What gets rendered

For a secret `mySecret` of an application deployed as `myapp`:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-mysecret
  namespace: <namespace>
  labels:
    app: myapp
spec:
  refreshInterval: "1h"
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: myapp-mysecret
    creationPolicy: Owner
  data:
    - secretKey: value
      remoteRef:
        key: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:my-secret"
        property: "password"
```

The operator creates a Kubernetes Secret named `myapp-mysecret` with the value under a
fixed `value` key. CloudHarness projects it into
`/opt/cloudharness/resources/secrets/myapp/mySecret`, so the application reads it with
`get_secret("mySecret")` like any other secret.

## Gotchas

* **API version.** The default is `external-secrets.io/v1beta1`, which recent operators
  still serve but have deprecated in favour of `external-secrets.io/v1`. Set
  `secretmanagers.aws.apiVersion: external-secrets.io/v1` on a cluster running ESO 0.17 or
  later; keep the default for older installs.
* **The store must exist before the release.** An `ExternalSecret` pointing at a missing
  store never produces its Secret, and the pod waits on the missing file. `kubectl describe
  externalsecret myapp-mysecret` reports the reason.
* **Versioned secrets.** `remoteRef.key` resolves to the current version. Pin a stage or
  version through the store or the ARN if you need a fixed one.
* **Moving an existing secret to this manager.** Delete the old entry from the application
  secret (`kubectl edit secret myapp`) as part of the upgrade, otherwise the same file is
  claimed twice and the pod fails to mount its secrets directory.

## Other AWS-backed managers

The `arn` and the store are settings rather than hardcoded values, so a second manager
reading from a different account or a different provider is a copy of
`managers/aws.tpl` with another store. See
[Adding a secret manager](../README.md#adding-a-secret-manager).

## References

* [External Secrets Operator](https://external-secrets.io/)
* [Getting started](https://external-secrets.io/latest/introduction/getting-started/)
* [AWS Secrets Manager provider](https://external-secrets.io/latest/provider/aws-secrets-manager/)
* [ExternalSecret API](https://external-secrets.io/latest/api/externalsecret/)
* Implementation: `deployment-configuration/helm/templates/secrets/managers/aws.tpl`
