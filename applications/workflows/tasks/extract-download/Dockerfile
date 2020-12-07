ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

ADD . /

ENV url 'https://www.google.com'
ENV shared_directory /

CMD env && python main.py $url $shared_directory $folder