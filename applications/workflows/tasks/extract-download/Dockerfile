FROM alpine
RUN apk update
RUN apk add file unzip wget

ADD . /

ENV url 'github.com/MetaCell/cloud-harness/blob/master/README.md'
ENV shared_directory /tmp

CMD source ./download.sh
