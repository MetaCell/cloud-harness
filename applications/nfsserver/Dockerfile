# compile provisioner
FROM golang:1.18.8 as provisioner

WORKDIR /usr/src/app
COPY provisioner/nfs-subdir-external-provisioner ./

RUN make

#
FROM k8s.gcr.io/volume-nfs:0.8

RUN yum install -y e4fsprogs rpcbind nfs-utils nfs-utils-lib

COPY --from=provisioner /usr/src/app/bin/nfs-subdir-external-provisioner /usr/local/bin/nfs-subdir-external-provisioner

COPY resources/*.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# COPY resources/run_nfs.sh /usr/local/bin/run_nfs.sh
# RUN chmod +x /usr/local/bin/run_nfs.sh

RUN echo "/exports *(rw,fsid=0,no_root_squash,no_subtree_check,crossmnt)" > /etc/exports
