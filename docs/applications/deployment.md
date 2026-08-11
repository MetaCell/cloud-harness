# Auto Deployments

CloudHarness can automatically generate a Kubernetes `Deployment` for any application by setting `harness.deployment.auto: true` in its `deploy/values.yaml`. This removes the need to write boilerplate Helm templates for standard services.

## Enabling auto deployment

```yaml
harness:
  deployment:
    auto: true
    port: 8080
```

When `auto: true`, CloudHarness generates:
- A `Deployment` with the configured container
- Standard environment variables injected into every container
- Volume mounts for CloudHarness resources and any configured secrets

> Auto deployment requires either a `Dockerfile` in the application directory, or an explicit `image` value.

## Configuration reference

All fields are under `harness.deployment`.

| Field | Type | Default | Description |
|---|---|---|---|
| `auto` | bool | `false` | Enable automatic deployment generation |
| `port` | int | `8080` | Container port |
| `replicas` | int | `1` | Number of pod replicas |
| `image` | string | *(from Dockerfile)* | Pre-built image to use instead of building from source |
| `name` | string | *(app name)* | Deployment name override |
| `command` | list | — | Override the container entrypoint |
| `args` | list | — | Override the container arguments |
| `resources` | object | see below | CPU and memory requests/limits |
| `volume` | object | — | Persistent volume — see [Volumes](./volumes.md) |
| `network` | object | — | Network policy — see [Network Policies](../network-policies.md) |
| `extraContainers` | map | `{}` | Init containers and sidecars — see [Extra Containers](#extra-containers) |

### Default resources

```yaml
harness:
  deployment:
    resources:
      requests:
        memory: "32Mi"
        cpu: "10m"
      limits:
        memory: "500Mi"
```

## Image

By default CloudHarness derives the image name from the application's `Dockerfile`. To use a pre-built or external image instead, set `image` explicitly:

```yaml
harness:
  deployment:
    auto: true
    image: nginx:1.25
```

When `image` is set, no `Dockerfile` is required and no build step is performed.

## Replicas

```yaml
harness:
  deployment:
    replicas: 3
```

Increasing replicas has implications for stateful operations like database migrations — see [running migrations with multiple replicas](#running-migrations-only-once-across-multiple-replicas).

## Command and args

Override the default image entrypoint or arguments:

```yaml
harness:
  deployment:
    command: ["gunicorn"]
    args: ["-w", "4", "-b", "0.0.0.0:8080", "myapp.wsgi"]
```

## Health probes

Liveness, readiness, and startup probes are configured under `harness` (not `harness.deployment`):

```yaml
harness:
  livenessProbe:
    path: /health
    port: 8080          # defaults to harness.deployment.port when omitted
    periodSeconds: 10
    failureThreshold: 3
    initialDelaySeconds: 0

  readinessProbe:
    path: /ready
    periodSeconds: 10
    failureThreshold: 3
    initialDelaySeconds: 0

  startupProbe:
    path: /health
    periodSeconds: 10
    failureThreshold: 30
    initialDelaySeconds: 0
```

All probes use HTTP GET.

## Resources

```yaml
harness:
  deployment:
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

Omitting `limits.cpu` removes the CPU cap entirely (the default).

## Environment variables

CloudHarness injects a standard set of environment variables into every container. Application-specific variables are defined via `envmap`. See [Environment Variables](./environment-variables.md).

## Volumes

Persistent volumes are configured under `harness.deployment.volume`. See [Volumes](./volumes.md).

## Network policies

Traffic rules are configured under `harness.deployment.network`. See [Network Policies](../network-policies.md).

---

## Extra containers

Extra containers let you attach additional containers to the pod. Two types are supported:

- **Init containers** — run to completion before the main container starts. Useful for database migrations, data seeding, or configuration bootstrapping.
- **Sidecar containers** — run alongside the main container for the lifetime of the pod. Useful for log shippers, proxies, or periodic background tasks.

### Configuration

Extra containers are defined under `harness.deployment.extraContainers`. Each key is the container name.

```yaml
harness:
  deployment:
    extraContainers:
      <container-name>:
        auto: true           # Required: set to true to include this container
        initContainer: true  # true = init container, false = sidecar
        image:               # Optional: defaults to the application image
        command: []          # Optional: command to run in the container
        shareVolume: false   # Optional: share the main container's volume mounts
        resources: {}        # Optional: defaults to the main container resources
```

#### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `auto` | bool | — | Must be `true` for the container to be included |
| `initContainer` | bool | — | `true` for init container, `false` for sidecar |
| `image` | string | Main app image | Docker image to use |
| `command` | list | `[]` | Container command (overrides image `CMD`/`ENTRYPOINT`) |
| `shareVolume` | bool | `false` | Mount the same volumes as the main container |
| `resources` | object | Main container resources | CPU/memory requests and limits |

If `image` is omitted, the extra container uses the same image as the main application container — the most common setup for init containers that run a different command against the same codebase.

If `resources` is omitted, the extra container inherits the main container's resource requests and limits.

Extra containers always receive the same environment variables as the main application container (`CH_CURRENT_APP_NAME`, the CloudHarness `CH_*` variables, deployment secrets and the application's `env`/`envmap` entries). Set `shareVolume: true` when the container also needs the CloudHarness configuration and secrets mounts (e.g. anything reading the application configuration, such as Django `manage.py` commands).

### Init containers

Init containers run sequentially before the main application container starts. Kubernetes restarts the pod if any init container fails, making them reliable for mandatory setup steps.

```yaml
harness:
  deployment:
    extraContainers:
      run-migrations:
        auto: true
        initContainer: true
        command: ["python", "manage.py", "migrate"]
        shareVolume: true
```

#### Running migrations only once across multiple replicas

When `replicas > 1`, all pods start at roughly the same time and each pod's init container would attempt the migration concurrently. Use a distributed lock to ensure migrations run exactly once.

The example below uses a PostgreSQL advisory lock. The replica that acquires the lock runs migrations; all others wait in a loop until the lock is released (meaning migration is done), then exit without re-running migrations.

```yaml
harness:
  deployment:
    replicas: 3
    extraContainers:
      run-migrations:
        auto: true
        initContainer: true
        command:
          - sh
          - -c
          - |
            python manage.py migrate --check 2>/dev/null && echo "No migrations needed" && exit 0
            if python manage.py dbshell -c "SELECT pg_try_advisory_lock(42)" | grep -q t; then
              echo "Acquired migration lock, running migrations..."
              python manage.py migrate
            else
              echo "Waiting for migrations to complete..."
              until python manage.py dbshell -c "SELECT pg_try_advisory_lock(42)" | grep -q t; do
                sleep 2
              done
              echo "Migrations complete"
            fi
```

For Django applications see the [django-base template](../../application-templates/django-base) for a ready-to-use example.

### Sidecar containers

Sidecar containers start with the main container and run for the full lifetime of the pod.

```yaml
harness:
  deployment:
    extraContainers:
      log-forwarder:
        auto: true
        initContainer: false
        image: fluent/fluent-bit:latest
        shareVolume: false
        resources:
          requests:
            memory: "32Mi"
            cpu: "10m"
          limits:
            memory: "64Mi"
```

### Volume sharing

Set `shareVolume: true` to give an extra container the same volume mounts as the main container:

```yaml
harness:
  deployment:
    volume:
      name: app-data
      mountpath: /data
      auto: true
      size: 1Gi
    extraContainers:
      seed-data:
        auto: true
        initContainer: true
        command: ["sh", "-c", "cp -r /defaults/* /data/"]
        shareVolume: true
```

---

## Complete example

```yaml
harness:
  deployment:
    auto: true
    port: 8080
    replicas: 2
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
    volume:
      name: app-data
      mountpath: /data
      auto: true
      size: 5Gi
    extraContainers:
      run-migrations:
        auto: true
        initContainer: true
        command: ["python", "manage.py", "migrate"]
        shareVolume: false
      beat-scheduler:
        auto: true
        initContainer: false
        command: ["python", "-m", "celery", "-A", "myapp", "beat"]
        shareVolume: false
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"

  livenessProbe:
    path: /health
    periodSeconds: 10
    failureThreshold: 3
    initialDelaySeconds: 10

  readinessProbe:
    path: /ready
    periodSeconds: 10
    failureThreshold: 3
    initialDelaySeconds: 5
```
