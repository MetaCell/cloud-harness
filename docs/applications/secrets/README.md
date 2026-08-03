# CloudHarness Secrets

## What secrets are

Kubernetes Secrets let you store and manage sensitive information, such as passwords, OAuth tokens, and ssh keys. Storing confidential information in a Secret is safer and more flexible than putting it verbatim in a Pod definition or in a container image. See [Secrets design document](https://github.com/kubernetes/design-proposals-archive/blob/main/auth/secrets.md) for more information.

**CloudHarness has build-in support for application specific kubernetes secrets.**

The CH secrets will be mounted as data volumes to be used by a container in a Pod and will be auto updated on change. This means that a pod doesn't need to be restarted to "see" the new value(s)

remark: an application has only access to it's "own" secrets

## Secret definition in CloudHarness

Secrets are defined in the application values.yaml file in the `secrets` section under the `harness` section.
Example

```yaml
harness:
  secrets:
    unsecureSecret: <value>
    secureSecret:
    random-static-secret: ""
    random-dynamic-secret: ?
```

Secret values are initialized in three different ways:
* Set the secret's value (as in `unsecureSecret`). Do that only if you aware of what you are doing as the value may be pushed in the git(hub) repository.
* Leave the secret's value `null` (as in `secureSecret`) to configure manually later in the ci/cd pipeline.
* Use the "" (empty string) value (as in `random-static-secret`) to let CloudHarness generate a random value for you. 
  This secret won't be updated after being set by any of the CloudHarness automations, so has to be managed through `kubectl` directly.
* Use the `?` value (as in `random-dynamic-secret`) to get a new random value for every deployment upgrade

Secret editing/maintenance alternatives:
* CI/CD Codefresh support: all `null` and `<value>` secrets will be added to the codefresh deployment file(s) and can be set/overwritten through the codefresh variable configuration
* Using Helm to set/overwrite the secret's value `helm ... --set apps.<appname>.harness.secrets.<secret>=<value>`
* Using kubernetes secret edit `kubectl edit secret <secret>`

## Secret managers

The values above are managed by CloudHarness itself. A secret can instead be delegated to a
secret manager, by replacing the plain value with a definition object:

```yaml
harness:
  secrets:
    mySecret:
      manager: onepassword
      default: "a value"
      path: vaults/my-vault/items/my-item
```

* `manager` selects who provides the value. When the key is missing, or is set to
  `cloudharness`, everything works exactly as described above, so the two forms are
  interchangeable: `mySecret: 'a value'` and `mySecret: {default: 'a value'}` are equivalent.
* `manager` set explicitly to null means **unmanaged**: CloudHarness renders nothing at all
  and assumes the secret entry already exists. Create it out of band, for instance with
  `kubectl edit secret <appname>`. The application secret is mounted as optional in that
  case, so a missing entry surfaces as a `SecretNotFound` at runtime rather than blocking
  the pod from starting.
* `default` is the value used by the `cloudharness` manager, and the fallback used when the
  secret manager is not available, as in local docker compose deployments. It follows the
  same conventions as a plain value, including `""` and `?`.
* Any other entry is manager specific: 1Password needs the item `path`, AWS needs the
  secret `arn`, and so on.

Whatever the manager, all the secrets of an application are exposed as files in the same
directory, so `get_secret` keeps working unchanged.

When moving an existing secret from `cloudharness` to another manager, delete the entry from
the application secret (`kubectl edit secret <appname>`) as part of the upgrade. CloudHarness
stops rendering the entry but does not remove the value already stored in the cluster, and
having it both in the application secret and in the one created by the manager makes the pod
fail to mount its secrets directory.

Secrets handled by a manager other than `cloudharness` are never exported as Codefresh
pipeline variables: their value does not come from the pipeline.

### Built-in managers

Every manager relies on an operator running in the cluster: CloudHarness renders the custom
resources, the operator is what reaches the external service. Each manager has its own page
covering the cluster setup, its settings and what it renders.

| Manager | Reads from | Needs | Page |
| --- | --- | --- | --- |
| `onepassword` | 1Password | [1Password Kubernetes Operator](https://developer.1password.com/docs/k8s/k8s-operator/) | [managers/onepassword.md](./managers/onepassword.md) |
| `aws` | AWS Secrets Manager | [External Secrets Operator](https://external-secrets.io/) | [managers/aws.md](./managers/aws.md) |

```yaml
harness:
  secrets:
    fromOnePassword:
      manager: onepassword
      path: vaults/my-vault/items/my-item
    fromAws:
      manager: aws
      arn: arn:aws:secretsmanager:eu-west-1:123456789012:secret:my-secret
```

Settings shared by all the secrets of a manager are configured once for the whole
deployment in the `secretmanagers` section of the root `values.yaml`, and can be overridden
secret by secret. This section is plain deployment configuration and ends up in the
`cloudharness-allvalues` config map: never put credentials in it, the manager authenticates
through its own operator configuration.

```yaml
secretmanagers:
  onepassword:
    vault: my-vault
  aws:
    store: aws-secrets-manager
    storeKind: ClusterSecretStore
    refreshInterval: 1h
```

### Adding a secret manager

A manager named `X` is defined by two Helm templates, which can be added by CloudHarness or
by any application in its `deploy/templates` folder:

* `deploy_utils.secretmanager.X.resource` renders the Kubernetes resources materializing
  the secret.
* `deploy_utils.secretmanager.X.ref` outputs `<kubernetes secret name>/<key>`, telling
  CloudHarness where the value ends up, so that it can be mounted with the other secrets of
  the application.

Both are called once per secret with the context
`(dict "root" $ "app" $app "name" <secret name> "spec" <secret definition> "resourceName" <name to use for the resource>)`,
where `spec` carries the manager specific settings and `resourceName` is a name safe to
give to the rendered resources. Use `deploy_utils.secretManagerSetting` to read a setting
from the secret, falling back to the manager's `secretmanagers.X` section.

Each built-in manager lives in its own file under
`deployment-configuration/helm/templates/secrets/managers/`, documenting its cluster
prerequisites, its settings and what it renders — `onepassword.tpl` and `aws.tpl` are the
two to copy from, with [managers/onepassword.md](./managers/onepassword.md) and
[managers/aws.md](./managers/aws.md) as the matching pages. The framework itself is in
`deployment-configuration/helm/templates/secrets/_secrets.tpl`.

## Secrets in Codefresh pipelines

Secrets defined under `harness.secrets` and handled by the `cloudharness` manager are also exported as
deployment variables in the automatically generated Codefresh pipeline. When the deployment step is
assembled, each secret name is transformed before being referenced in the pipeline:

- Any underscore (`_`) in the secret name is replaced by a double underscore (`__`).
- The resulting string is converted to upper case to form the environment variable name.

For example a secret declared as `db_password` becomes the variable `DB__PASSWORD` in Codefresh and will
appear in the deployment step as:

```
custom_values:
  - apps_<appname>_harness_secrets_db__password=${{DB__PASSWORD}}
```

The same underscore replacement is applied to the application name in the `custom_values` entry.

Secrets declared in the rich form have their value nested under `default`, so the entry becomes
`apps_<appname>_harness_secrets_db__password_default=${{DB__PASSWORD}}`.

## Secret usage in Python backend apps

The CloudHarness python library (`cloudharness-common`) provides easy access to the CH secrets, just import `get_secrets` from `cloudharness.utils.secrets`.

Example:
```python
from cloudharness.utils.secrets import get_secret
secret1_value = get_secret("Secret1")
print(f"Secret1 = {secret1_value}")
```

Hint: make sure the secret's value is read on every use, remember that secrets can be changed "on the fly"

