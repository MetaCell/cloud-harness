ARG NODE=node:22-alpine
ARG PYTHON=python:3.12-slim-trixie

FROM $NODE AS frontend

WORKDIR /app
COPY frontend/package.json .
COPY frontend/yarn.lock .
RUN yarn install --timeout 60000

COPY frontend .
RUN yarn build

#####

FROM $PYTHON

ENV MODULE_NAME=backend
ENV PORT=8080
ENV WORKERS=2
ENV APP_DIR=/usr/src/app
ENV PRODUCTION=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip && \
    pip install pytest --prefer-binary

# Vendored CloudHarness libraries: install requirements first to keep them cached
COPY libraries/models/requirements.txt /libraries/models/requirements.txt
COPY libraries/cloudharness-common/requirements.txt /libraries/cloudharness-common/requirements.txt
COPY libraries/cloudharness-django/requirements.txt /libraries/cloudharness-django/requirements.txt
RUN --mount=type=cache,target=/root/.cache \
    pip install --prefer-binary \
    -r /libraries/models/requirements.txt \
    -r /libraries/cloudharness-common/requirements.txt \
    -r /libraries/cloudharness-django/requirements.txt

COPY libraries /libraries
RUN pip install --no-cache-dir \
    -e /libraries/models \
    -e /libraries/cloudharness-common \
    -e /libraries/cloudharness-django

ARG DEBUG
RUN if [ -z "$DEBUG" ] ; then pip install debugpy --prefer-binary ; else echo "Debug not supported" ; fi

# Application
WORKDIR ${APP_DIR}
RUN mkdir -p ${APP_DIR}/static/www

COPY backend/requirements.txt ${APP_DIR}
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt --prefer-binary

COPY backend/requirements.txt backend/setup.py ${APP_DIR}
RUN python3 -m pip install -e .

COPY backend ${APP_DIR}
# collectstatic needs a secret key, not used at runtime
RUN DJANGO_SECRET_KEY=collectstatic-only python3 manage.py collectstatic --noinput

COPY --from=frontend /app/dist ${APP_DIR}/static/www

ENTRYPOINT uvicorn --workers ${WORKERS} --host 0.0.0.0 --port ${PORT} django_baseapp.asgi:application
