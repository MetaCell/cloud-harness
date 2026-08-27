ARG CLOUDHARNESS_BASE

FROM $CLOUDHARNESS_BASE

COPY libraries/cloudharness-utils/requirements.txt /libraries/cloudharness-utils/requirements.txt
RUN pip install --uploaded-prior-to=P7D -r /libraries/cloudharness-utils/requirements.txt --no-cache-dir

COPY tools/cloudharness-test/requirements.txt /tools/cloudharness-test/requirements.txt
RUN pip install --uploaded-prior-to=P7D -r /tools/cloudharness-test/requirements.txt --no-cache-dir

COPY libraries/cloudharness-utils /libraries/cloudharness-utils
RUN pip install --uploaded-prior-to=P7D -e /libraries/cloudharness-utils

COPY tools/cloudharness-test /tools/cloudharness-test
RUN pip install --uploaded-prior-to=P7D -e /tools/cloudharness-test