ARG CLOUDHARNESS_FLASK

FROM $CLOUDHARNESS_FLASK as frontend

ENV MODULE_NAME=volumemanager

ENV WORKERS=2
ENV PORT=8080

COPY requirements.txt /usr/src/app/

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip3 install --no-cache-dir -r requirements.txt  --prefer-binary

COPY . /usr/src/app

RUN pip3 install -e .

ENTRYPOINT gunicorn --workers=$WORKERS --bind=0.0.0.0:$PORT $MODULE_NAME.__main__:app
