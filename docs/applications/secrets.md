## CloudHarness Secrets

### What secrets are

Kubernetes Secrets let you store and manage sensitive information, such as passwords, OAuth tokens, and ssh keys. Storing confidential information in a Secret is safer and more flexible than putting it verbatim in a Pod definition or in a container image. See [Secrets design document](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/auth/secrets.md) for more information.

**CloudHarness has build-in support for application specific kubernetes secrets.**

The CH secrets will be mounted as data volumes to be used by a container in a Pod and will be auto updated on change. This means that a pod doesn't need to be restarted to "see" the new value(s)

remark: an application has only access to it's "own" secrets

### Secret definition in CloudHarness

Secrets are defined in the application values.yaml file in the `secrets` section under the `harness` section.
Example

```yaml
harness:
  secrets:
    Secret1: <value>
    SecondSecret:
    third-secret:
```

It is a wise decision to store the secret's `<value>` outside the git(hub) repository and leave the secret's value `null` / ommit it.

CloudHarness supports 3 ways for editing/maintenance of the secrets outside the git(hub) repository:
* Codefresh support, all secrets will be added to the codefresh deployment file(s) and can be set/overwritten through the codefresh variable configuration
* Using Helm to set/overwrite the secret's value `helm ... --set apps.<appname>.harness.secrets.<secret>=<value>`
* Using kubernetes secret edit `kubectl edit secret <secret>`

### Secret usage in Python backend apps

The CloudHarness python library (`cloudharness-common`) provides easy access to the CH secrets, just import `get_secrets` from `cloudharness.utils.secrets`.

Example:
```python
from cloudharness.utils.secrets import get_secret
secret1_value = get_secret("Secret1")
print(f"Secret1 = {secret1_value}")
```

Hint: make sure the secret's value is read on every use, remember that secrets can be changed "on the fly"