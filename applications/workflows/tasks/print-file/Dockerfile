ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE

ADD . /

ENV file_path /

CMD python ./main.py $file_path