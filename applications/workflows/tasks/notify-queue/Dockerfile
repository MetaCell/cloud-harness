ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

ADD . /

ENV workflow_result 'Failure'
ENV queue_name 'None'
ENV payload '{}'

CMD python main.py ${workflow_result} ${queue_name} ${payload}
