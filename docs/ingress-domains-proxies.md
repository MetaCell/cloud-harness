# Ingress, domains and proxies

## Default configurations for domain and subdomains
Cloud Harness makes it very easy to configure domains and proxies, by making
an underlying assumption:

- Applications share a main base domain (say ch.org)
- Applications can define a subdomain (say myapp)

The main domain is configured in the [root values file](../deployment-configuration/values-template.yaml) and
it is usually overridden by the `harness-deployment` command, e.g.

```
harness-deployment ... -d ch.org
```

The subdomain is defined in the application's values.yaml file in 
harness.subdomain (see for instance the [samples application configuration](../applications/samples/deploy/values.yaml))

For instance on applications/myapp/deploy/values.yaml:

```yaml
harness:
  subdomain: myapp
```

The above configurations put together create an ingress configuration for https://myapp.ch.org and automatically configure letsencrypt to create and renew certificates.

Note:
that the tls and letsencrypt configurations are enabled by default but should usually be disabled locally with

```
harness-deployment ... -dtls -l
```

## Main application

The "main" application is deployed on the base domain.
In order to specify a main application, override the value in your `/deployment-configuration/values-template.yaml` file.

Example
```yaml
mainapp: myapp
```
This creates a reverse proxy to https://ch.org pointing to myapp

## Proxy configurations

Ingress is a reverse proxy and as such has some configurations to take into account.
The most common configurations are connection timeouts and payload size.

To configure it, override the following values in your `deployment-configuration/values-template.yaml` file.

```yaml
proxy:
  timeout:
    # -- Timeout for proxy connections in seconds.
    send: 60
    # -- Timeout for proxy responses in seconds.
    read: 60
    keepalive: 60
  payload:
    # -- Maximum size of payload in MB
    max: 250
```

Note that in the case that gatekeepers are enabled, the same configurations are applied
to the gatekeepers, unless the application override them on `harness.proxy.*`.
See also the [gatekeepers documentation](./accounts.md#secure-and-enpoint-with-the-gatekeeper).