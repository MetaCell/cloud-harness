FROM python:3.10-alpine
ENV DEPLOY_DIR=deployment

COPY . cloudharness_utilities
RUN pip install ./cloudharness_utilities

RUN apk --update add git less openssh && \
    rm -rf /var/lib/apt/lists/* && \
    rm /var/cache/apk/*

WORKDIR $DEPLOY_DIR

CMD ['python', 'deployment-generate.py']
