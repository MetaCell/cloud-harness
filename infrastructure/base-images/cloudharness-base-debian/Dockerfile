ARG PARENT=python:3.7.6
FROM ${PARENT}

COPY libraries/cloudharness-common /libraries/cloudharness-common
COPY libraries/client/cloudharness_cli /client/cloudharness_cli

RUN pip install /libraries/cloudharness-common
RUN pip install /libraries/client/cloudharness_cli

WORKDIR /