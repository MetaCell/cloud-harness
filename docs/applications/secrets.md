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

## Secret usage in Python backend apps

The CloudHarness python library (`cloudharness-common`) provides easy access to the CH secrets, just import `get_secrets` from `cloudharness.utils.secrets`.

Example:
```python
from cloudharness.utils.secrets import get_secret
secret1_value = get_secret("Secret1")
print(f"Secret1 = {secret1_value}")
```

Hint: make sure the secret's value is read on every use, remember that secrets can be changed "on the fly"