ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

RUN apk add curl file

ADD . /

ENV url 'https://www.google.com'
ENV shared_directory /

CMD env && source ./download.sh
