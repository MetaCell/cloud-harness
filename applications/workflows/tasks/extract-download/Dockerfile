ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE

RUN apk add curl file unzip

ADD . /

ENV url 'https://www.google.com'
ENV shared_directory /

CMD env && source ./download.sh
