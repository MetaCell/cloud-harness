ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
#RUN apk add psycopg2 libpq-dev python-dev

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
