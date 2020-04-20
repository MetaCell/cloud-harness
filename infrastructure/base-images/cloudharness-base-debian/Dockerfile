ARG PARENT=python:3.7.6
FROM ${PARENT}

COPY libraries/cloudharness-common /libraries/cloudharness-common

RUN pip install /libraries/cloudharness-common

WORKDIR /