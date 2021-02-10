ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-flask:${TAG}

ENV MODULE_NAME=common

ENV WORKERS=2
ENV PORT=8080

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
# TODO: @Sinnema can this be removed?
#RUN apk add psycopg2 libpq-dev python-dev

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV FLASK_ENV=production
ENV APP_SETTINGS=common.config.ProductionConfig