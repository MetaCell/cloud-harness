ARG CLOUDHARNESS_FLASK

FROM $CLOUDHARNESS_FLASK as frontend

ENV MODULE_NAME=volumemanager

ENV WORKERS=2
ENV PORT=8080

COPY pylock.toml /usr/src/app/

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip3 install --no-cache-dir -r pylock.toml  --prefer-binary

COPY . /usr/src/app

RUN pip3 install --uploaded-prior-to=P7D -e .
