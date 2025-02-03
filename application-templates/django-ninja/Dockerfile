ARG CLOUDHARNESS_FRONTEND_BUILD
ARG CLOUDHARNESS_DJANGO

FROM $CLOUDHARNESS_FRONTEND_BUILD AS frontend

ARG APP_DIR=/app

WORKDIR ${APP_DIR}
COPY frontend/package.json .
COPY frontend/yarn.lock .
RUN yarn install --timeout 60000

COPY frontend .
RUN yarn build

#####

FROM $CLOUDHARNESS_DJANGO

WORKDIR ${APP_DIR}
RUN mkdir -p ${APP_DIR}/static/www

COPY backend/requirements.txt ${APP_DIR}
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip3 install --no-cache-dir -r requirements.txt --prefer-binary

COPY backend/requirements.txt backend/setup.py ${APP_DIR}
RUN python3 -m pip install -e .

COPY backend ${APP_DIR}
RUN python3 manage.py collectstatic --noinput

COPY --from=frontend /app/dist ${APP_DIR}/static/www

ENTRYPOINT uvicorn --workers ${WORKERS} --host 0.0.0.0 --port ${PORT} django_baseapp.asgi:application
