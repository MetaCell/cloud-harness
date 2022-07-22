ARG CLOUDHARNESS_FRONTEND_BUILD
ARG CLOUDHARNESS_DJANGO

FROM $CLOUDHARNESS_FRONTEND_BUILD as frontend

ENV APP_DIR=/app

WORKDIR ${APP_DIR}
COPY frontend/package.json ${APP_DIR}
COPY frontend/package-lock.json ${APP_DIR}
RUN npm ci

COPY frontend ${APP_DIR}
RUN npm run build

#####

FROM $CLOUDHARNESS_DJANGO

WORKDIR ${APP_DIR}
RUN mkdir -p ${APP_DIR}/static/www

COPY backend/requirements.txt ${APP_DIR}
RUN pip3 install --no-cache-dir -r requirements.txt

COPY backend/requirements.txt backend/setup.py ${APP_DIR}
RUN python3 -m pip install -e .

COPY backend ${APP_DIR}
RUN python3 manage.py collectstatic --noinput

COPY --from=frontend /app/dist ${APP_DIR}/static/www

ENTRYPOINT uvicorn --workers ${WORKERS} --host 0.0.0.0 --port ${PORT} main:app
