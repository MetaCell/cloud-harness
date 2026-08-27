ARG PARENT=python:3.12-slim-trixie
FROM ${PARENT}

RUN apt update && apt install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    nfs-common \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install --uploaded-prior-to=P7D pytest  --prefer-binary

COPY libraries/models/requirements.txt /libraries/models/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install --uploaded-prior-to=P7D -r /libraries/models/requirements.txt  --prefer-binary
COPY libraries/cloudharness-common/requirements.txt /libraries/cloudharness-common/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install --uploaded-prior-to=P7D -r /libraries/cloudharness-common/requirements.txt  --prefer-binary
COPY libraries/client/cloudharness_cli/requirements.txt /libraries/client/cloudharness_cli/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install --uploaded-prior-to=P7D -r /libraries/client/cloudharness_cli/requirements.txt  --prefer-binary

COPY libraries/models /libraries/models
RUN pip install --uploaded-prior-to=P7D -e /libraries/models --no-cache-dir

COPY libraries/cloudharness-common /libraries/cloudharness-common
COPY libraries/client/cloudharness_cli /libraries/client/cloudharness_cli

RUN pip install --uploaded-prior-to=P7D -e /libraries/models --no-cache-dir
RUN pip install --uploaded-prior-to=P7D -e /libraries/cloudharness-common --no-cache-dir
RUN pip install --uploaded-prior-to=P7D -e /libraries/client/cloudharness_cli --no-cache-dir

ARG DEBUG
RUN if [ -z "$DEBUG" ] ; then pip install --uploaded-prior-to=P7D debugpy --prefer-binary ; else echo "Debug not supported" ; fi

WORKDIR /
