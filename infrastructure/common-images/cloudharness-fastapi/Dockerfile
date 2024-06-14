ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE

ENV MODULE_NAME=backend
ENV PORT=8080
ENV WORKERS=2
ENV APP_DIR=/usr/src/app

COPY libraries/fastapi/requirements.txt /tmp
RUN  --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
     python3 -m pip install -r /tmp/requirements.txt --prefer-binary && \
     rm /tmp/requirements.txt
