ARG PARENT=python:3.7.6-alpine
FROM ${PARENT}

RUN apk update
RUN apk upgrade
RUN apk add bash

COPY libraries/cloudharness-common /libraries/cloudharness-common

RUN pip install /libraries/cloudharness-common

WORKDIR /