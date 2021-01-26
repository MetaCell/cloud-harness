ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

ENV DIR=/usr/src/app
# Override module name in sub image
ENV MODULE_NAME=app
ENV WORKERS=2
ENV PORT=8080

WORKDIR $DIR

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE $PORT
ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app