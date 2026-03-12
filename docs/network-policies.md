# Network Policies

Cloud Harness provides automatic network policy management to control traffic flow between applications and external networks. Network policies enforce zero-trust networking principles by default and can be configured per application.

## Overview

Network policies in Kubernetes define how pods can communicate with each other and with external networks. Cloud Harness automatically generates NetworkPolicy resources based on application configuration, providing security boundaries while maintaining necessary communication paths.

## Default Behavior

By default, when network policies are enabled for an application:

- **Same-namespace traffic**: Always allowed in both directions — all pods in the same namespace can always communicate freely
- **DNS**: Always allowed (port 53 TCP/UDP) for egress
- **Cross-namespace / external traffic**: Blocked by default
- **`ingress: true`**: The `Ingress` policyType is omitted entirely — Kubernetes leaves all incoming traffic unrestricted
- **`egress: true`**: The `Egress` policyType is omitted entirely — Kubernetes leaves all outgoing traffic unrestricted
- **Both `ingress: true` + `egress: true`**: No NetworkPolicy is generated at all

## Enabling Network Policies

### Application deployments

Network policies for application pods are opt-in. To enable them, add a `network` key under `harness.deployment` in the application's `deploy/values.yaml`:

```yaml
harness:
  deployment:
    auto: true
    network:
      ingress: false
      egress: false
```

### Databases

Database pods always have a network policy generated automatically when `harness.database.auto: true`. The default is fully restrictive (same-namespace only). Configuration lives under `harness.database.network`:

```yaml
harness:
  database:
    auto: true
    network:
      ingress: false  # default — same-namespace only
      egress: false   # default — same-namespace only
```

The same `ingress`, `egress`, and `allowedNamespaces` options available for application deployments apply to databases.

## Configuration Options

### Ingress Policy

```yaml
harness:
  deployment:
    network:
      ingress: true
```

Controls traffic arriving at the pod **from other namespaces and the external internet**. Same-namespace traffic is always allowed regardless of this setting.

When `ingress: true` + `egress: true`:
- No NetworkPolicy is created — the pod is fully unrestricted

When `ingress: true` (and `egress: false`):
- The `Ingress` policyType is omitted from the NetworkPolicy — Kubernetes treats ingress as fully open
- Egress is still restricted to same-namespace pods and DNS

When `ingress: false` (default):
- The `Ingress` policyType is enforced: only same-namespace pods (and any `allowedNamespaces`) can reach this pod

### Egress Policy

```yaml
harness:
  deployment:
    network:
      egress: true
```

Controls traffic leaving the pod **to other namespaces and the external internet**. Same-namespace traffic and DNS are always allowed regardless of this setting.

When `egress: true` (and `ingress: false`):
- The `Egress` policyType is omitted from the NetworkPolicy — Kubernetes treats egress as fully open
- Ingress is still restricted to same-namespace pods (and any `allowedNamespaces`)

When `egress: false` (default):
- The `Egress` policyType is enforced: only same-namespace pods and DNS (port 53) can receive traffic from this pod

Private IP ranges are **not** explicitly blocked — when `egress: true`, the policyType is simply absent and all destinations are reachable.

### Namespace Whitelisting

For fine-grained cross-namespace access without fully opening a direction, specific namespaces can be whitelisted:

```yaml
harness:
  deployment:
    network:
      ingress: false
      egress: false
      allowedNamespaces:
        - monitoring
        - logging
```

Whitelisted namespaces are allowed both as **ingress sources** and **egress destinations**, but only for **restricted directions** (`ingress: false` / `egress: false`). If a direction is already open (`ingress: true` or `egress: true`), the whitelist has no effect on it.

This is useful for:

- Granting access to a monitoring namespace (e.g. Prometheus scraping metrics)
- Allowing a logging agent in another namespace to receive logs
- Enabling selective cross-namespace service communication without fully opening the policy

Namespaces are matched by the `kubernetes.io/metadata.name` label, which Kubernetes automatically assigns to all namespaces since version 1.21. On older clusters, or namespaces created before upgrading, this label may need to be added manually:

```bash
kubectl label namespace <name> kubernetes.io/metadata.name=<name>
```

> **Note**: For ingress controllers (Traefik, nginx, etc.) prefer `ingress: true` over whitelisting the ingress controller namespace. Ingress controllers proxy external traffic and `ingress: true` removes the policyType entirely — no label dependency required.

## Complete Example

An internal API that is reachable only by the ingress controller (egress restricted to same-namespace and a monitoring namespace):

```yaml
harness:
  subdomain: api
  
  deployment:
    auto: true
    name: my-api
    network:
      ingress: true   # ingress controller (Traefik/nginx) runs in a different namespace
      egress: false   # restrict outgoing traffic
      allowedNamespaces:
        - monitoring  # allow Prometheus to scrape metrics
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
```

This generates a NetworkPolicy that:
1. Omits the `Ingress` policyType — all incoming traffic is unrestricted (suitable for ingress controllers)
2. Enforces `Egress`: only same-namespace pods, DNS, and the `monitoring` namespace are reachable
3. Always allows intra-namespace pod communication

## Network Policy Resource

The generated NetworkPolicy with `ingress: false`, `egress: false`, and `allowedNamespaces: [monitoring]`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-api-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: my-api
  policyTypes:
    - Ingress   # present: ingress is restricted
    - Egress    # present: egress is restricted
  ingress:
    # Always: same namespace
    - from:
        - podSelector: {}
    # allowedNamespaces whitelist
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
  egress:
    # Always: same namespace
    - to:
        - podSelector: {}
    # Always: DNS
    - ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
    # allowedNamespaces whitelist
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
```

With `ingress: true`, `egress: false` — the `Ingress` policyType is simply absent, so Kubernetes imposes no ingress restrictions:

```yaml
  policyTypes:
    - Egress    # only egress is restricted
  egress:
    - to:
        - podSelector: {}
    - ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
```

## Security Considerations

### Zero-Trust Approach

When network policies are enabled, Cloud Harness implements a zero-trust model:
- **Same-namespace free**: Pods within the same namespace can always communicate without restriction
- **Cross-namespace / external deny by default**: Traffic requires explicit opt-in via `ingress`/`egress` flags or `allowedNamespaces`
- **Open by omission**: Setting `ingress: true` or `egress: true` removes that policyType from the NetworkPolicy entirely, letting Kubernetes leave that direction unrestricted — no extra rules needed
- **Full open = no policy**: When both flags are true, no NetworkPolicy is generated

### Best Practices

1. **Enable Network Policies**: Enable network policies on applications that handle sensitive data or provide critical services

2. **Prefer whitelisting over full open**: Use `allowedNamespaces` for selective cross-namespace access rather than setting `ingress: true` or `egress: true` when only specific namespaces need access

3. **`ingress: true` for externally exposed apps**: Applications with public endpoints (subdomain/domain) need this to allow traffic from the ingress controller in its own namespace

4. **`egress: true` for apps calling external APIs**: Only enable when the application genuinely needs to reach the public internet

5. **Testing**: Test network policies in development environments before deploying to production

## Common Use Cases

### Public Web Application

Exposes a public endpoint via the Kubernetes Ingress controller (Traefik, nginx, etc. — which typically runs in a different namespace). Use `ingress: true` to remove the Ingress policyType entirely; do **not** rely on `allowedNamespaces` for ingress controllers:

```yaml
harness:
  subdomain: webapp
  deployment:
    network:
      ingress: true  # removes Ingress policyType — no namespace label dependency
      egress: true   # allow calls to external APIs
```

### Backend API

Serves requests from the ingress controller and calls external services:

```yaml
harness:
  subdomain: api
  deployment:
    network:
      ingress: true
      egress: true
```

### Internal Microservice

Only reachable within the namespace, no external connectivity:

```yaml
harness:
  deployment:
    network:
      ingress: false
      egress: false
```

Same-namespace pods can still communicate freely; all cross-namespace and internet traffic is blocked.

### Database Service

Accepts connections from same namespace only, but also scraped by Prometheus in the `monitoring` namespace:

```yaml
harness:
  database:
    auto: true
    network:
      allowedNamespaces:
        - monitoring
```

### Shared Service with Selective Cross-Namespace Access

A service used by applications in multiple namespaces:

```yaml
harness:
  deployment:
    network:
      ingress: false
      egress: false
      allowedNamespaces:
        - team-a
        - team-b
```

## Troubleshooting

### Same-namespace communication not working

Same-namespace pod-to-pod communication is always allowed when a network policy exists. If it fails:
1. Verify that the network policy was actually generated (the `network:` key must be present in values)
2. Check that the CNI plugin on your cluster supports NetworkPolicy

### Cross-namespace communication failing

If applications in different namespaces cannot communicate:
1. Ensure `ingress: true` is set on the destination app, or the source namespace is in `allowedNamespaces`
2. Ensure `egress: true` is set on the source app, or the destination namespace is in `allowedNamespaces`
3. Verify both apps are deployed with their network policies active

### External API calls failing

If external API calls timeout:
1. Ensure `egress: true` is configured on the calling application
2. Verify DNS resolution works (should always be allowed)
3. Check that the target IP is not in a private range (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) — these are always blocked

### Ingress controller not routing traffic

If Traefik, nginx, or another ingress controller cannot reach the application:
1. **Use `ingress: true`**, not `allowedNamespaces`. Ingress controllers run in a separate namespace and proxy external traffic — `ingress: true` removes the `Ingress` policyType entirely, which is simpler and has no label dependency.
2. Avoid patterns like `allowedNamespaces: [traefik]` for ingress controllers: this relies on the namespace having the `kubernetes.io/metadata.name: traefik` label, which may not exist on all clusters or may use a different namespace name (e.g. `traefik-system`).
3. Verify the application has `subdomain` or `domain` configured so that the Ingress resource is created.

### Namespace whitelist not working

If a whitelisted namespace cannot reach the application:
1. Verify the namespace has the `kubernetes.io/metadata.name` label (automatic in Kubernetes 1.21+, may need manual labelling on older clusters or namespaces created before the upgrade):
   ```bash
   kubectl get namespace <name> --show-labels
   kubectl label namespace <name> kubernetes.io/metadata.name=<name>
   ```
2. Check the exact namespace name matches the value in `allowedNamespaces` (e.g. `traefik-system` vs `traefik`)
3. Remember that `allowedNamespaces` only applies to **restricted directions**: if `ingress: true` the whitelist has no effect on ingress (it's already fully open); same for egress

## Configuration Reference

Documentation on network policies and deployment configuration can be found in:
- [Applications Configuration](./applications/README.md) - Application values.yaml reference
- [Deployment Configuration](../deployment-configuration/README.md) - Cluster deployment settings
- Kubernetes [Network Policies Documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
