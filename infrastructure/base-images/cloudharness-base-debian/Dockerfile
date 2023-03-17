ARG PARENT=python:3.9.10
FROM ${PARENT}

RUN apt-get update && apt-get install -y nfs-common && rm -rf /var/lib/apt/lists/*

RUN pip install pytest --no-cache-dir
COPY libraries/models/requirements.txt /libraries/models/requirements.txt
RUN pip install -r /libraries/models/requirements.txt --no-cache-dir
COPY libraries/cloudharness-common/requirements.txt /libraries/cloudharness-common/requirements.txt
RUN pip install -r /libraries/cloudharness-common/requirements.txt --no-cache-dir
COPY libraries/client/cloudharness_cli/requirements.txt /libraries/client/cloudharness_cli/requirements.txt
RUN pip install -r /libraries/client/cloudharness_cli/requirements.txt --no-cache-dir

COPY libraries/models /libraries/models
RUN pip install -e /libraries/models --no-cache-dir

COPY libraries/cloudharness-common /libraries/cloudharness-common
COPY libraries/client/cloudharness_cli /libraries/client/cloudharness_cli

#
RUN pip install -e /libraries/models --no-cache-dir
RUN pip install -e /libraries/cloudharness-common --no-cache-dir
RUN pip install -e /libraries/client/cloudharness_cli --no-cache-dir

WORKDIR /