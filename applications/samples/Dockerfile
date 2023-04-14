ARG CLOUDHARNESS_FRONTEND_BUILD
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
ENV MODULE_NAME=samples

ENV WORKERS=2
ENV PORT=8080

COPY backend/requirements.txt /usr/src/app/

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip3 install -r requirements.txt  --prefer-binary

COPY backend/ /usr/src/app

COPY --from=frontend app/dist/ /usr/src/app/www

RUN pip3 install -e .

CMD gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app --timeout 180