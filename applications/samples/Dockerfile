ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-frontend-build:${TAG} as frontend

ENV APP_DIR=/app

WORKDIR ${APP_DIR}
COPY frontend/package.json ${APP_DIR}
COPY frontend/package-lock.json ${APP_DIR}
RUN npm ci

COPY frontend ${APP_DIR}
RUN npm run build

#####

ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-flask:${TAG}

ENV MODULE_NAME=samples

ENV WORKERS=2
ENV PORT=8080

COPY backend/requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY backend/ /usr/src/app

COPY --from=frontend app/dist/ /usr/src/app/www

