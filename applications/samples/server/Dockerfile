ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-flask:${TAG}

ENV MODULE_NAME=samples

ENV WORKERS=2
ENV PORT=8080

COPY . /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app