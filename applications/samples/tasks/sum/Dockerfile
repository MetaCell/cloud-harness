ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

ADD . /

ENV a 0
ENV b 0

CMD python main.py $a $b