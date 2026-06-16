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
  # -- Set to false to hide remote client headers. Will hide the client IPs in all logs
  forwardedHeaders: true
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
See also the [gatekeepers documentation](./accounts.md#secure-and-endpoint-with-the-gatekeeper).

## Route pattern configuration

Cloud Harness allows customizing which request paths are routed to an application
via paths and regular expression. There are two levels where this can be set:

- **Global**: `ingress.path` and `ingress.pathType` in `deployment-configuration/helm/values.yaml` (applies to all apps by default).
- **Application**: `harness.gateway.path` and `harness.gateway.pathType` in an application's `values.yaml` (overrides the global value for that app).

The Helm ingress template uses the application-level `harness.gateway` when present,
falling back to the global `ingress` otherwise.

The default configuration uses Prefix paths for the highest compatibility:

```yaml
path: /
pathType: Prefix
```
The default configuration will work for a single application being served in the root directory within the domain with no exclusions.


Example with regular expression (global default in `deployment-configuration/helm/values.yaml`):

```yaml
ingress:
  # Example regex segment for routes (used in paths like '/(pattern)')
  path: "/(.*)"
  pathType: ImplementationSpecific
```

Example (application override in `applications/<app>/deploy/values.yaml`):

```yaml
harness:
  # route_pattern is used to build the Ingress path for the app
  path: '/((?!(?:metrics)(?:/)?$).*)' # exclude only '/metrics' and '/metrics/'
  pathType: ImplementationSpecific
```

Customization notes:
- The pattern is inserted into the generated Ingress `path` field. Make sure the regex
  is valid for your ingress controller and matches the expected path syntax.

## TLS and Let's Encrypt

TLS is enabled by default for non-local deployments. Cloud Harness provisions a
`cert-manager` ACME `Issuer` named `letsencrypt-<namespace>` and annotates every
generated Ingress (and Gateway, when using the Gateway API) so that certificates
are obtained and renewed automatically.

All configuration lives under `ingress.letsencrypt` in
`deployment-configuration/helm/values.yaml`:

```yaml
ingress:
  letsencrypt:
    enabled: true                       # provision the ACME Issuer
    email: cloudharness@metacell.us     # ACME account email
    privateKeySecretName: tls-secret-issuer  # ACME account private-key Secret
    solvers: []                         # solver list; empty = http01 default
    secrets: {}                         # credential Secrets created in-namespace
```

### Default — public domains via http01

For publicly reachable domains, the defaults are sufficient. Set `email` and
leave the rest untouched:

```yaml
ingress:
  letsencrypt:
    email: ops@example.com
```

This renders a single `http01` solver bound to the configured `ingressClass`.
HTTP01 requires no credentials, so the rest of this section only applies to
DNS01 setups.

### Defining credential secrets

Every DNS01 solver references its provider credentials through a `*SecretRef`
block (the exact field name depends on the provider — `apiTokenSecretRef`,
`tokenSecretRef`, `secretAccessKeySecretRef`, `serviceAccountSecretRef`,
`clientSecretSecretRef`, `tsigSecretSecretRef`, …). All of them have the same
shape:

```yaml
someProviderSecretRef:
  name: <kubernetes-secret-name>   # name of the Secret in the release namespace
  key:  <data-key-inside-secret>   # which field of the Secret holds the credential
```

You have two options for providing the referenced Secret:

**Option 1 — declare it inline (Cloud Harness creates it):** add an entry under
`ingress.letsencrypt.secrets`. The top-level key becomes the `Secret`'s name;
the nested map becomes its `stringData`. Each inner key is one credential
field, and the `*SecretRef.key` in the solver must match one of those inner
keys exactly.

```yaml
ingress:
  letsencrypt:
    secrets:
      cloudflare-api-token:        # → Secret/cloudflare-api-token
        api-token: s3cr3t          # → stringData.api-token = "s3cr3t"
      route53-credentials:         # → Secret/route53-credentials
        secret-access-key: AKIA... # → stringData.secret-access-key = "AKIA..."
```

A single Secret can hold multiple keys, so you can group related credentials
together (e.g. an `accessKey` and a `secretAccessKey`) and reference each by
its own key. Names you choose for both the Secret and its keys are arbitrary —
the only constraint is that the `*SecretRef.name`/`key` in the solver match.

Because `values.yaml` is committed to source control, prefer injecting real
secrets via environment-variable interpolation at deploy time:

```yaml
ingress:
  letsencrypt:
    secrets:
      cloudflare-api-token:
        api-token: ${CLOUDFLARE_API_TOKEN}   # resolved by harness-deployment
```

**Option 2 — provision the Secret out-of-band:** create the `Secret` with any
external tool (`kubectl create secret`, sealed-secrets, External Secrets
Operator, a CI/CD pipeline secret, etc.) in the same namespace as the Issuer.
Leave `ingress.letsencrypt.secrets` empty and just reference the existing
Secret from the solver.

```bash
kubectl -n ch create secret generic cloudflare-api-token \
  --from-literal=api-token="$CLOUDFLARE_API_TOKEN"
```

```yaml
ingress:
  letsencrypt:
    # secrets: {}  ← intentionally omitted; the Secret already exists
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
```

Both options are interchangeable from cert-manager's perspective — pick the
one that matches how you manage other secrets in the cluster.

### DNS01 — Cloudflare (non-public domains)

DNS01 challenges work for any domain — including domains that aren't reachable
from the internet — as long as cert-manager can update the zone's TXT records.

```yaml
ingress:
  letsencrypt:
    email: ops@example.com
    secrets:
      cloudflare-api-token:
        api-token: ${CLOUDFLARE_API_TOKEN}
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
```

The `secrets:` map materializes a `Secret` per entry in the release namespace.
Skip it if you provision credentials out-of-band (sealed-secrets, External
Secrets, manual `kubectl create secret`, etc.) — only the `solvers` entry is
required in that case.

### Multiple solvers (mixed http01 + DNS01)

Selectors route hostnames to the matching solver. Default solver applies to
anything that doesn't match a selector:

```yaml
ingress:
  letsencrypt:
    email: ops@example.com
    secrets:
      cloudflare-api-token: { api-token: ${CLOUDFLARE_API_TOKEN} }
    solvers:
      - http01:
          ingress:
            class: nginx
      - dns01:
          cloudflare:
            apiTokenSecretRef: { name: cloudflare-api-token, key: api-token }
        selector:
          dnsZones: ["internal.example.com"]
```

### Other DNS providers

Any provider supported by `cert-manager` works — the `solvers[*].dns01` block
is passed through verbatim. Each provider expects credentials via a
`*SecretRef` (see [Defining credential secrets](#defining-credential-secrets)).
Common shapes:

```yaml
# --- Route 53 ---
secrets:
  route53-credentials:
    secret-access-key: ${AWS_SECRET_ACCESS_KEY}
solvers:
  - dns01:
      route53:
        region: us-east-1
        accessKeyID: AKIA...
        secretAccessKeySecretRef: { name: route53-credentials, key: secret-access-key }

# --- Google Cloud DNS ---
secrets:
  clouddns-sa:
    key.json: ${GCP_SERVICE_ACCOUNT_JSON}   # entire JSON service-account file
solvers:
  - dns01:
      cloudDNS:
        project: my-gcp-project
        serviceAccountSecretRef: { name: clouddns-sa, key: key.json }

# --- DigitalOcean ---
secrets:
  digitalocean-dns:
    access-token: ${DO_TOKEN}
solvers:
  - dns01:
      digitalocean:
        tokenSecretRef: { name: digitalocean-dns, key: access-token }
```

See the [cert-manager DNS01 reference](https://cert-manager.io/docs/configuration/acme/dns01/)
for the full per-provider schema (Azure DNS, RFC2136, AcmeDNS, webhook, …).

### Bring your own certificates (no ACME)

Set `letsencrypt.enabled: false` to skip the ACME Issuer and the
`cert-manager.io/issuer` annotation on every generated Ingress/Gateway. Each
app's Ingress still references a Secret named `tls-secret-<appName>`, and
Cloud Harness can populate that Secret for you in two ways (used together).

**Option 1 — file-based shared cert.** Drop a PEM cert pair at
`resources/certs/tls.crt|key` inside the Helm chart. It is applied to every
app that has a `subdomain`, `domain`, or `aliases`, useful when a single
wildcard cert covers the whole base domain. Same files that already drive
local-mode TLS.

```yaml
ingress:
  letsencrypt:
    enabled: false
```

```
deployment-configuration/helm/resources/certs/
├── tls.crt   # PEM-encoded cert (or chain)
└── tls.key   # PEM-encoded private key
```

**Option 2 — per-app inline certs.** Map each app to its own PEM cert/key
under `ingress.tls.certs`. Each entry materializes as one
`tls-secret-<appName>` of type `kubernetes.io/tls`. Per-app entries override
the file-based shared cert for that app — apps without an entry fall back to
the shared cert. Use env-variable interpolation to keep raw PEM out of
committed YAML:

```yaml
ingress:
  letsencrypt:
    enabled: false
  tls:
    certs:
      myapp:
        crt: ${MYAPP_TLS_CRT}
        key: ${MYAPP_TLS_KEY}
      analytics:
        crt: ${ANALYTICS_TLS_CRT}
        key: ${ANALYTICS_TLS_KEY}
```

**Option 3 — fully out-of-band.** Leave `ingress.tls.certs` empty and don't
stage cert files. No `Secret` is rendered by the chart, and you create each
`tls-secret-<appName>` separately with whatever tooling you already use
(`kubectl create secret tls`, sealed-secrets, External Secrets Operator, a CI
job, cloud LB integration, …). The app key must match `harness.name` /
`harness.service.name` so the Ingress reference resolves.

```bash
kubectl -n ch create secret tls tls-secret-myapp \
  --cert=path/to/myapp.crt --key=path/to/myapp.key
```

> **Gateway-API mode.** When deploying via `Gateway` + `HTTPRoute` instead of
> Ingress, the gateway uses a single shared `tls-secret` Secret (not per-app).
> Per-app `ingress.tls.certs` entries don't apply in that mode — provide the
> shared cert via the file-based path or out-of-band.

### Disabling TLS entirely

For local or development deployments, set `tls: false` at the root of the
values file. This is what `harness-deployment ... -dtls -l` does for you.
