ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-flask:${TAG}

ENV MODULE_NAME=common

ENV WORKERS=2
ENV PORT=8080

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV FLASK_ENV=production
ENV APP_SETTINGS=common.config.ProductionConfig