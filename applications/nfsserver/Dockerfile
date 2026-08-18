# compile provisioner
FROM golang:1.26 AS provisioner

WORKDIR /usr/src/app
COPY nfs-subdir-external-provisioner ./

RUN go mod tidy && make

# compile nfsvol (mount manager / watchdog)
FROM golang:1.26 AS nfsvol

WORKDIR /usr/src/nfsvol
COPY nfsvol/ ./
RUN go mod tidy && go build -o /usr/local/bin/nfsvol .

#
# Upstream continuation of the old k8s.gcr.io/volume-nfs:0.8 image, maintained
# by the Kubernetes project at test/images/volume/nfs. CentOS Stream 9 base
# with nfs-utils already installed; we only need to add e2fsprogs for mkfs.ext4.
FROM rockylinux/rockylinux:10.1-minimal

RUN microdnf install -y \
  e2fsprogs \
  rpcbind \
  nfs-utils \
  && microdnf clean all

COPY --from=provisioner /usr/src/app/bin/nfs-subdir-external-provisioner /usr/local/bin/nfs-subdir-external-provisioner
COPY --from=nfsvol /usr/local/bin/nfsvol /usr/local/bin/nfsvol

COPY resources/*.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh /usr/local/bin/nfsvol

RUN echo "/exports *(rw,fsid=0,insecure,no_subtree_check,no_root_squash,crossmnt)" > /etc/exports

CMD ["/usr/local/bin/run_nfs.sh"]
