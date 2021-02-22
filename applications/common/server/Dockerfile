ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_FLASK=${REGISTRY}cloudharness-flask:${TAG}

FROM $CLOUDHARNESS_FLASK

ENV MODULE_NAME=common

ENV WORKERS=2
ENV PORT=8080
RUN apk update
RUN apk add postgresql-dev

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV FLASK_ENV=production
ENV APP_SETTINGS=common.config.ProductionConfig
RUN pip3 install -e /usr/src/app
ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app