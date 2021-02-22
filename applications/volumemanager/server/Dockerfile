ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_FLASK=${REGISTRY}cloudharness-flask:${TAG}

FROM $CLOUDHARNESS_FLASK as frontend

ENV MODULE_NAME=volumemanager

ENV WORKERS=2
ENV PORT=8080

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN pip3 install -e .

ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app
