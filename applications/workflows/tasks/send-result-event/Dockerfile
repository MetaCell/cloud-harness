ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

ADD . /

ENV shared_directory /mnt/shared

CMD python main.py $shared_directory