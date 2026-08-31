# Application Volume

Application Volumes are defined at `harness.deployment.volume`.
CloudHarness supports only one volume per deployment.

The Application Volume will be mounted in the container at a specific path at **deployment** time.

## Auto volume creation and mount

This can be established through setting the `auto` attribute (default false) of the Volume object
- `auto: true` --> auto create the volume and mount
- `auto: false` --> only mount the volume

Shared volumes are handy when you have e.g. 2 deployments for one app: frontend & backend deployment
in such a case it could be helpfull that the frontend can access files stored by the backend.
E.g. user uploaded media files

**Example**

```yaml
harness:
  ...
  deployment:
    ...
    volume:
      name: my-first-volume
      mountpath: /usr/src/app/myvolume
      auto: true
      size: 5Gi
      usenfs: false
```

## Shared volumes
A Volume can be mounted by one or more pods (shared Volume). Be careful: only one of the deployments
should create the Volume, the other deployment should only mount it.

By default Cloudharness uses the `standard` StorageClass for the volume and ReadWriteOnce
mount strategy. 
In order to support volume sharing affinity rules are added so that all pods using
the same volume end up in the same node.
This strategy works for basic use cases but can easily cause deadlocks if more than
one node is available on the cluster and other affinity rules or taints are present.

### Storage class

The volume `storageClass` sets the storage class of the claim; when not specified, `standard` is
used. Set it to null to omit the storage class from the claim, so that the cluster default storage
class provisions the volume:

```yaml
harness:
  ...
  deployment:
    ...
    volume:
      name: my-volume
      mountpath: /usr/src/app/myvolume
      auto: true
      size: 5Gi
      storageClass: null   # or e.g. gp3
```

The same setting is available for database volumes as `harness.database.storageClass` (see
[databases](databases.md)).

### ReadWriteMany volumes

Setting `writeMany: true` creates and mounts the volume as ReadWriteMany. A ReadWriteMany volume
attaches to several nodes at the same time, hence the pods using it are not pinned to the volume's
node: no podAffinity is added, and deployments roll normally instead of being recreated.

ReadWriteMany requires a storage class supporting it (e.g. AWS EFS, Azure Files, CephFS,
the nfs provisioner). The default `standard` class is normally ReadWriteOnce only, so set
`storageClass` to a ReadWriteMany capable class (or to null when the cluster default one supports
ReadWriteMany).

```yaml
harness:
  ...
  deployment:
    ...
    volume:
      name: my-shared-volume
      mountpath: /usr/src/app/myvolume
      auto: true
      size: 5Gi
      writeMany: true
      storageClass: efs-sc
```

When a volume is shared by several deployments, declare the same `writeMany` on all of them: the
claim is created once (by the deployment declaring `auto: true`), but each deployment decides on
its own declaration whether its pods are pinned to the volume's node.

Note that both the access mode and the storage class are immutable on an existing
PersistentVolumeClaim: changing `writeMany` or the storage class on a live volume requires
deleting and recreating the claim, and the data is not migrated.

### Using the NFS server application

Volume sharing can also be achieved by using the Network File System provided by the `nfsserver`
application. In order to use the nfs, the nfs server must be added to the deployment (e.g. as a
dependency) and `usenfs` must be set to true: the volume is created as ReadWriteMany on the storage
class of the nfs provisioner.

```yaml
harness:
  ...
  dependencies:
    ...
    hard:
    - nfsserver
    ...
  deployment:
    ...
    volume:
      name: my-shared-volume
      mountpath: /usr/src/app/myvolume
      auto: true
      size: 5Gi
      usenfs: true
```

`usenfs` is equivalent to `writeMany: true` with the nfs provisioner storage class, and is kept
for backwards compatibility: on a cluster providing a ReadWriteMany storage class, prefer
`writeMany` with `storageClass`.

The nfs server settings prevail on the volume ones: an `usenfs` volume is always created on the
nfs provisioner storage class and mounted ReadWriteMany, whatever `storageClass` and `writeMany`
say. `harness-deployment` logs a warning when they collide:

```
WARNING Volume my-shared-volume of application samples sets usenfs and storageClass efs-sc: the nfs server storage class prevails.
```

### Volumes mounted by Argo workflows

Argo workflow pods mounting an application volume (`<volume name>:<mount path>`, see
[Argo workflows](../argo-workflows.md)) are pinned to the volume's node in the same way
deployments are. ReadWriteMany application volumes are recognized from the application
configuration, so their workflows get no node pinning.

Volumes that are not declared by an application can be marked as ReadWriteMany explicitly with
the `rwx` mount mode, which also disables the pinning:

```python
operations.PipelineOperation('my-op-', tasks, shared_directory='my-claim:/mnt/shared:rwx')
```

## Deploying as a StatefulSet

By default, a deployment with a ReadWriteOnce volume is rendered as a Kubernetes `Deployment` with
a `Recreate` update strategy and podAffinity pinning it to the node holding the volume, since a
ReadWriteOnce volume can only attach to one node at a time.

Setting `harness.deployment.statefulset: true` renders it as a `StatefulSet` instead. StatefulSet
updates terminate the old pod before creating its replacement, so neither the `Recreate` strategy
nor node pinning is needed.

```yaml
harness:
  ...
  deployment:
    ...
    statefulset: true
    volume:
      name: my-volume
      mountpath: /usr/src/app/myvolume
      auto: true
      size: 5Gi
```

The volume is provisioned per replica through `volumeClaimTemplates` (PVCs named
`<volume>-<app>-<ordinal>`). Exceptions: ReadWriteMany volumes (`writeMany: true` or
`usenfs: true`) and externally managed volumes (`auto: false`) keep mounting their common PVC by
name — per-replica claims would un-share them.

**Migrating from an existing Deployment**: if a PVC named after the volume exists in the cluster
at deploy time (left over from the pre-statefulset Deployment), it is treated as a legacy volume:

- it is kept in the release with `helm.sh/resource-policy: keep`, so Helm never deletes it;
- a `<name>-volume-migration` Job is deployed that mounts the legacy volume (read-only) and
  streams its data through the Kubernetes API (tar over `kubectl exec`, as `kubectl cp` does)
  into each statefulset pod. The legacy and statefulset volumes are never mounted by the same
  pod, so the migration also works on multi-zone/multi-region clusters where the two volumes
  may not be attachable to the same node;
- each statefulset pod runs a `volume-migration` init container that mounts only the pod's own
  volume and holds the pod until the job has copied the data into it (guarded by a
  `.cloudharness-volume-migrated` marker, so each volume is migrated exactly once).

Once the migration is verified, delete the legacy PVC (`kubectl delete pvc <volume-name>`): the
next deployment drops the migration job, its RBAC resources and the init container gate. Note
that the data flows through the Kubernetes API server: for very large volumes consider a manual
migration instead.

Note that `volumeClaimTemplates` are immutable once created: changing `volume.size` afterwards
won't resize the PVCs and requires a manual resize. Flipping the flag on a live release causes
Helm to delete the Deployment and create the StatefulSet, with a brief window of downtime while
the volume detaches and reattaches.

### Routing writes to a single pod (leader service)

For a StatefulSet (with `harness.service.auto: true`), an additional service named `<service-name>-rw` is automatically created that
always resolves to pod 0. This supports a single-writer pattern when running multiple replicas
over a shared volume: any pod can serve reads, but write requests are handled only by pod 0.

Writes can be routed to the leader in two ways:

- **From the application**: forward mutating requests to `http://<service-name>-rw` when the pod
  is not the leader (inside a pod, `HOSTNAME` equals the pod name, so the leader check is
  `HOSTNAME == "<deployment-name>-0"`). This is the most reliable option, as only the
  application knows which requests actually write.
- **From the ingress**: declare the write endpoints in `harness.uri_role_mapping` with their
  `methods`; uris declaring a write method (POST/PUT/PATCH/DELETE) are routed to the leader
  service instead of the load-balanced one:

  ```yaml
  harness:
    ...
    deployment:
      statefulset: true
      replicas: 3
    uri_role_mapping:
      - uri: /api/edit/*
        methods: [POST, PUT, PATCH, DELETE]
      - uri: /api/upload
        methods: [POST]
  ```

  Routing granularity is the uri, not the method (plain Kubernetes Ingress cannot match methods),
  so all requests to those uris — including GETs — go to pod 0. On secured applications the same
  `methods` field restricts the gatekeeper resource to those methods, and leader routing applies
  only to `white-listed` uris (which bypass the gatekeeper by design): routing a secured uri
  around the auth proxy would bypass authentication, so non-white-listed write endpoints must
  forward writes at the application level. See the samples application `/api/write-file`
  endpoint for a working example.

Note that pod 0 restarts last during rolling updates, but while it restarts write requests fail:
clients should retry. Also mind that after a write, replicas may briefly serve stale reads (see
the NFS caching notes above).