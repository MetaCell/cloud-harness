# compile provisioner
FROM golang:1.26.2 AS provisioner

WORKDIR /usr/src/app
COPY nfs-subdir-external-provisioner ./

RUN make

#
FROM k8s.gcr.io/volume-nfs:0.8

RUN yum install -y \
    e2fsprogs \
    nfs-utils \
    rpcbind \
    && yum clean all \
    && rm -rf /var/cache/yum

COPY --from=provisioner /usr/src/app/bin/nfs-subdir-external-provisioner /usr/local/bin/nfs-subdir-external-provisioner

COPY resources/*.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

RUN echo "/exports *(rw,fsid=0,insecure,no_subtree_check,no_root_squash,crossmnt)" > /etc/exports

CMD ["/usr/local/bin/run_nfs.sh"]
