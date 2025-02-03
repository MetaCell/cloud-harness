ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE as base

FROM quay.io/jupyterhub/k8s-hub:3.2.1
USER root


COPY --from=base  libraries/models/requirements.txt /libraries/models/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install -r /libraries/models/requirements.txt
COPY --from=base  libraries/cloudharness-common/requirements.txt /libraries/cloudharness-common/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install -r /libraries/cloudharness-common/requirements.txt
COPY --from=base  libraries/client/cloudharness_cli/requirements.txt /libraries/client/cloudharness_cli/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install -r /libraries/client/cloudharness_cli/requirements.txt

COPY --from=base  libraries/models /libraries/models
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
   pip install -e /libraries/models

COPY --from=base  libraries/cloudharness-common /libraries/cloudharness-common
COPY --from=base  libraries/client/cloudharness_cli /libraries/client/cloudharness_cli

#

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
   pip install -e /libraries/cloudharness-common
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
   pip install -e /libraries/client/cloudharness_cli


COPY src src
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install ./src/harness_jupyter
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip install ./src/chauthenticator

USER jovyan
