ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_FRONTEND_BUILD=${REGISTRY}cloudharness-frontend-build:${TAG}
ARG CLOUDHARNESS_FLASK

FROM $CLOUDHARNESS_FRONTEND_BUILD as frontend

ENV APP_DIR=/app

WORKDIR ${APP_DIR}
COPY frontend/package.json ${APP_DIR}
COPY frontend/package-lock.json ${APP_DIR}
RUN npm ci

COPY frontend ${APP_DIR}
RUN npm run build

#####

FROM $CLOUDHARNESS_FLASK

ENV MODULE_NAME=__APP_NAME__

ENV WORKERS=2
ENV PORT=8080

COPY backend/requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY backend/ /usr/src/app
RUN pip3 install -e .

COPY --from=frontend app/dist/ /usr/src/app/www

ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app