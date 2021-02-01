ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

RUN apk add postgresql-dev python3-dev musl-dev

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080

ENV FLASK_ENV=production
ENV APP_SETTINGS=common.config.ProductionConfig

ENTRYPOINT ["python3"]

CMD ["-m", "common"]
