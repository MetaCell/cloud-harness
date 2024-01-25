ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE as base
RUN apt update && apt install -y file unzip wget

ADD . /

ENV url 'github.com/MetaCell/cloud-harness/blob/master/README.md'
ENV shared_directory /tmp

CMD source ./download.sh
