ARG PARENT=python:3.7.6-alpine
FROM ${PARENT}

RUN apk update
RUN apk upgrade

# Add bash for k8s console
RUN apk add bash
# dev tools needed by some python libraries
RUN apk add gcc libc-dev g++ python3-dev libffi-dev openssl-dev

COPY libraries/cloudharness-common /libraries/cloudharness-common
COPY client/cloudharness_cli /client/cloudharness_cli

RUN pip install /libraries/cloudharness-common
RUN pip install /client/cloudharness_cli

WORKDIR /