ARG PARENT=python:3.9.10-alpine
FROM ${PARENT}

RUN apk update
RUN apk upgrade

# Add bash for k8s console
RUN apk add bash
# dev tools needed by some python libraries
RUN apk add gcc libc-dev g++ python3-dev libffi-dev openssl-dev rust musl-dev cargo

COPY libraries/models/requirements.txt /libraries/models/requirements.txt
RUN pip install -r /libraries/models/requirements.txt
COPY libraries/cloudharness-common/requirements.txt /libraries/cloudharness-common/requirements.txt
RUN pip install -r /libraries/cloudharness-common/requirements.txt
COPY libraries/client/cloudharness_cli/requirements.txt /libraries/client/cloudharness_cli/requirements.txt
RUN pip install -r /libraries/client/cloudharness_cli/requirements.txt

COPY libraries/models /libraries/models
RUN pip install -e /libraries/models

COPY libraries/cloudharness-common /libraries/cloudharness-common
COPY libraries/client/cloudharness_cli /libraries/client/cloudharness_cli

#

RUN pip install -e /libraries/cloudharness-common
RUN pip install -e /libraries/client/cloudharness_cli

WORKDIR /
