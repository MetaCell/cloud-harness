ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_FLASK=${REGISTRY}cloudharness-flask:${TAG}

ENV MODULE_NAME=__APP_NAME__
ENV WORKERS=2
ENV PORT=8080

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN pip3 install -e .

ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app
