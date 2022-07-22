ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE

ENV MODULE_NAME=backend
ENV PORT=8080
ENV WORKERS=2
ENV APP_DIR=/usr/src/app

ENV PRODUCTION=true

COPY libraries/cloudharness-django /libraries/cloudharness-django
COPY libraries/fastapi/requirements.txt /tmp

RUN  apk add jpeg-dev zlib-dev git && \
     python3 -m pip install --upgrade pip && \
     python3 -m pip install -r /tmp/requirements.txt && \
     python3 -m pip install -e /libraries/cloudharness-django --no-cache-dir --upgrade && \
     rm /tmp/requirements.txt
