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

Cloudharness uses the `standard` StorageClass for the volume and ReadWriteOnce
mount strategy. 
In order to support volume sharing affinity rules are added so that all pods using
the same volume end up in the same node.
This strategy works for basic use cases but can easily cause deadlocks if more than
one node is available on the cluster and other affinity rules or taints are present.

A better support for volume sharing is achieved by using a Network File System (NFS).
In order to use the nfs, the NFS must be added to the deployment (e.g. as a dependency and `usenfs` must be set to true.

```
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