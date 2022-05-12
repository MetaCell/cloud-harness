# Environments

Different deployments often require different configurations.
For instance, we may want to assign less resources/replicas to a pod deployed locally
respect to the production build.

## How to set the environment

The environment of the current deployment can ve set with the parameter `--env` (`-e`)
of `harness-deployment`.

When the environment is set, specific environment configuration files are included, potentially overriding any value in the system.

The environment-specific configuration files have the same name of the "main" file,
with the suffix 
For example, after running
```
harness-deployment cloud-harness . -e dev
```

the following configuration files are potentially loaded (if they exist):

- `deployment-configuration/values-template-dev.yaml`
- `deployment-configuration/codefresh-template-dev.yaml`

And for each application:

- `deploy/values-dev.yaml`

The precedence of overriding gives precedence to the specific environment files as in the following example:

- `./cloud-harness/deployment-configuration/values-template.yaml`
```yaml
a: 1
b: 1
c: 1
d: 1
```
- `./cloud-harness/deployment-configuration/values-template-dev.yaml`
```yaml
b: 2
c: 2
```
- `./deployment-configuration/values-template.yaml`
```yaml
c: 3
```
- `./deployment-configuration/values-template-dev.yaml`
```yaml
d: 4
```

The resulting configuration will be

```yaml
a: 1
b: 2
c: 3
d: 4
```

## Multiple environments

Multiple environments can be set by separating different environments with an hyphen, like `-e env1-env2`

For example, by running 

```
harness-deployment cloud-harness . -e dev-test
```

We get the following loading order:

```
values.yaml
values-dev.yaml
values-test.yaml
```

The same principle applies to all templates.