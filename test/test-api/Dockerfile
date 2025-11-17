ARG CLOUDHARNESS_BASE

FROM $CLOUDHARNESS_BASE

ENV CH_VALUES_PATH=/codefresh/volume/cloud-harness

# Install cloudharness-utils first (required by other packages)
COPY libraries/cloudharness-utils/requirements.txt /libraries/cloudharness-utils/requirements.txt
RUN pip install -r /libraries/cloudharness-utils/requirements.txt --no-cache-dir

COPY libraries/cloudharness-utils /libraries/cloudharness-utils
RUN pip install -e /libraries/cloudharness-utils

# Install deployment-cli-tools (depends on cloudharness-utils)
COPY tools/deployment-cli-tools /tools/deployment-cli-tools
RUN pip install -e /tools/deployment-cli-tools

# Install cloudharness-test (depends on both above)
COPY tools/cloudharness-test /tools/cloudharness-test
RUN pip install -e /tools/cloudharness-test