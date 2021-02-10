ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-flask:${TAG}

ENV MODULE_NAME=workflows_api

COPY . /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app