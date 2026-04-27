# NFS Server — Production Caveats

This NFS server is a pragmatic, single-replica design that trades some
durability for operational simplicity. The defaults favour **client-pod
availability over write durability**: during a server outage, applications
see `EIO` and are expected to retry, rather than hanging indefinitely.

Read this before relying on it for production workloads.

## Architecture

- One NFS server pod (single-replica Deployment, `strategy: Recreate`).
- Backing storage: one RWO PVC (`nfs-exports`) holding per-PVC ext4 loopback
  files at `/exports/<pv>.quota`, mounted at `/exports/<pv>`.
- Clients mount via a stable ClusterIP Service + DNS FQDN, with
  `soft,nolock,local_lock=all,nfsvers=3`.
- Per-PVC exports are written to `/etc/exports.d/` with a deterministic
  SHA-256-derived fsid, so client file handles survive server pod restarts.

## Outage behaviour

| Trigger | Outage duration (for active client pods) | Client-visible error |
|---|---|---|
| `kubectl delete pod nfs-server-...` | seconds (kube reschedules immediately) | brief `EIO`, then resumes transparently (fsid stable) |
| `kubectl rollout restart` | seconds — Recreate waits for old pod first | brief `EIO`, then resumes |
| Graceful node drain of NFS node | ~30–60 s (PVC detach + reattach) | brief `EIO`, then resumes |
| **Ungraceful node loss** (node crash, network partition) | **up to ~6 minutes** (force-detach timeout) | `EIO` repeatedly until pod reattaches on another node |
| Loopback goes stale on same host (rare) | up to 30 s (watchdog period) | transparent, clients do not notice |

The ~6 minute ungraceful-loss window is inherent to RWO storage with
cloud-provider CSI drivers and cannot be eliminated without switching to a
different storage strategy (see "Not suitable for" below).

## Application requirements

Applications that use PVCs from this provisioner **must**:

- Tolerate `EIO` on reads and writes. Retry with backoff. The current config
  uses `soft` mount semantics — I/O returns an error rather than hanging.
- Not rely on POSIX file-range locking (`flock`, `fcntl`) across pods.
  `nolock,local_lock=all` disables cross-client locking. Shared-writer
  workloads (e.g. SQLite, cooperating text editors) will race silently.
- Not assume write-through durability during an outage. In-flight writes
  that return `EIO` may or may not have reached disk.

## What these caveats rule out

This backend is **not suitable for**:

- Databases that require fsync durability semantics (use a proper database
  PVC, not NFS).
- Workloads with multiple writers to the same file across nodes.
- Strict HA requirements (no failover during ungraceful node loss).
- Large cross-region deployments (single RWO PVC is region-local).

It **is suitable for**:

- Shared read-only / append-only data between pods (logs, content).
- Cache / scratch volumes where a brief `EIO` is retryable.
- Shared artifact storage between producer and consumer pods.

## Operator responsibilities

### Backup

`nfs-exports` is a single cloud PVC with no built-in backup. If lost, every
NFS-backed PVC in the cluster is lost. Operators must:

- Schedule snapshots of `nfs-exports` (cloud-provider-specific).
- Store snapshots in a separate region/account for real DR.

Neither `nfsvol` nor the provisioner automates this. It is intentional; DR
policy is a per-deployment decision.

### Graceful node migration

To move the NFS server pod to a different node:

1. Cordon the target node preferences as needed.
2. Either cordon+drain the source node (standard flow), or
3. `kubectl delete pod nfs-server-...` — the pod terminates, PVC detaches,
   and a new pod schedules on any eligible node.

With `podDisruptionBudget.enabled: true` in `values.yaml`, `kubectl drain`
will be blocked by the PDB. This is intentional — forces the operator to
use the explicit delete-pod flow so automated tooling does not evict
unaware.

### Monitoring

- `/healthz` on port 8080 exposes the watchdog health (readiness and
  liveness probes already consume this).
- Watch for `watchdog: remount failed` log lines — indicates the loopback
  layer is inconsistent with `/exports/*.quota`.
- Watch for `mount-all: N of M mounts failed` at startup.

## Not addressed by this iteration

- Multi-region / cross-cluster replication.
- Automated snapshot scheduling.
- Active/passive HA (would need shared block storage + fencing, or a move
  to a managed NFS service — EFS, Filestore, Azure Files).

If any of those become requirements, switch to a managed NFS or a proper
CSI driver. This backend was designed for small, single-region, best-effort
shared storage.
