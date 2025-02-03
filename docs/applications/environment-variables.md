# CloudHarness Environment Variables

CloudHarness has support for adding environment variables for an application which will be available to all containers within the application pod.

## Automatically included environment variables

The following environment variables are included in each container by default:
- `CH_CURRENT_APP_NAME`: the name of the application
- Any environment variables defined in the root `.Values.env`
- If `accounts` is an included application:
    - `CH_ACCOUNTS_CLIENT_SECRET`: the client secret for the accounts
    - `CH_ACCOUNTS_REALM`: the accounts realm
    - `CH_ACCOUNTS_AUTH_DOMAIN`: the auth domain for the accounts
    - `CH_ACCOUNTS_CLIENT_ID`: the client id for the accounts
    - `DOMAIN`: the domain for the accounts

## Environment variables definition in CloudHarness

Environment variables are defined in the application values.yaml file in the `envmap` section under the `harness` section.
Example

```yaml
harness:
  envmap:
    ENV_VARIABLE_A: <value>
    ...
```

Each key in the `envmap` will add an environment variable with a name matching the key and a value equal to the value provided. The value can be any primitive type, but will be quoted as a string within the deployment template.

### (Deprecated) Setting with `env`

Environment variables can be defined by using the `env` section under the `harness` section. This functionality is deprecated but not yet obsoleted, and use of `envmap` should be preferred over this approach.
Example

```yaml
harness:
  env:
  - name: ENV_VARIABLE_A
    value: <value>
  ...
```

Each element of the `env` sequence will add an environment variable named `name` with value set from `value`.

This functionality was deprecated as cloud harness cannot merge arrays, so if an environment variable needed changing in a specific environment the entire array must be reproduced to change the single variable.