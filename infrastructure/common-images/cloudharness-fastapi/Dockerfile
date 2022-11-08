ARG CLOUDHARNESS_BASE_DEBIAN
FROM $CLOUDHARNESS_BASE_DEBIAN

ENV MODULE_NAME=backend
ENV PORT=8080
ENV WORKERS=2
ENV APP_DIR=/usr/src/app

COPY libraries/fastapi/requirements.txt /tmp
RUN  python3 -m pip install --upgrade pip && \
     python3 -m pip install -r /tmp/requirements.txt --no-cache-dir && \
     rm /tmp/requirements.txt
