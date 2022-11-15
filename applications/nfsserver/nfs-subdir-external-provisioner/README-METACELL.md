# Kubernetes NFS Subdir External Provisioner - MetaCell Build

See also the CloudHarness NFS server implementation <https://github.com/MetaCell/cloud-harness>

## Build, tag and push

```bash
make

docker build . -t nfs-subdir-external-provisioner:latest

docker tag nfs-subdir-external-provisioner:latest us.gcr.io/metacellllc/nfs-subdir-external-provisioner:latest

docker push us.gcr.io/metacellllc/nfs-subdir-external-provisioner:latest
```
