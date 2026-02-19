ARG CLOUDHARNESS_FRONTEND_BUILD
ARG CLOUDHARNESS_FLASK

FROM $CLOUDHARNESS_FRONTEND_BUILD as frontend

ARG TEST_ARGUMENT=default
RUN echo $TEST_ARGUMENT

ENV APP_DIR=/app

WORKDIR ${APP_DIR}
COPY frontend/package.json ${APP_DIR}
COPY frontend/yarn.lock ${APP_DIR}
RUN yarn install --frozen-lockfile --timeout 60000

COPY frontend ${APP_DIR}
RUN yarn build

#####
FROM $CLOUDHARNESS_FLASK
ENV MODULE_NAME=samples

ENV WORKERS=2
ENV PORT=8080

COPY backend/requirements.txt /usr/src/app/

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip3 install -r requirements.txt  --prefer-binary

COPY backend/ /usr/src/app

COPY --from=frontend app/dist/ /usr/src/app/www

RUN pip3 install -e .
