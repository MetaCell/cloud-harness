ARG REGISTRY
ARG TAG=latest
FROM ${REGISTRY}cloudharness-base:${TAG}

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080
RUN pip3 install -e .
ENTRYPOINT ["python3"]

CMD ["-m", "workflows_api"]