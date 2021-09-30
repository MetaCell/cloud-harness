ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE as base

FROM jupyterhub/k8s-hub:0.9.0
USER root

COPY --from=base /libraries/cloudharness-common /libraries/cloudharness-common
COPY --from=base /libraries/client/cloudharness_cli /libraries/client/cloudharness_cli

RUN pip install -e /libraries/cloudharness-common
RUN pip install -e /libraries/client/cloudharness_cli

COPY src src
RUN pip install ./src/harness_jupyter
RUN pip install ./src/chauthenticator

RUN chmod 777 /usr/local/lib/python3.6/dist-packages/  -R
USER jovyan
