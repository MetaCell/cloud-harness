ARG CLOUDHARNESS_BASE

FROM $CLOUDHARNESS_BASE

COPY libraries/cloudharness-utils/requirements.txt /libraries/cloudharness-utils/requirements.txt
RUN pip install -r /libraries/cloudharness-utils/requirements.txt --no-cache-dir

COPY tools/deployment-cli-tools/requirements.txt /tools/deployment-cli-tools/requirements.txt
RUN pip install -r /tools/deployment-cli-tools/requirements.txt --no-cache-dir

COPY tools/cloudharness-test/requirements.txt /tools/cloudharness-test/requirements.txt
RUN pip install -r /tools/cloudharness-test/requirements.txt --no-cache-dir

COPY libraries/cloudharness-utils /libraries/cloudharness-utils
RUN pip install -e /libraries/cloudharness-utils

COPY tools/deployment-cli-tools /tools/deployment-cli-tools
RUN pip install -e /tools/deployment-cli-tools

COPY tools/cloudharness-test /tools/cloudharness-test
RUN pip install -e /tools/cloudharness-test