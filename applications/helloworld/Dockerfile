ARG CLOUDHARNESS_FLASK
FROM $CLOUDHARNESS_FLASK

ENV MODULE_NAME=helloworld
ENV WORKERS=2
ENV PORT=8080

COPY server/requirements.txt /usr/src/app/
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt --prefer-binary

COPY server/ /usr/src/app

ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app
