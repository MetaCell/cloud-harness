ARG ARGO_GOLANG=golang:1.19.13-bullseye
ARG ARGO_CONTROLLER=quay.io/argoproj/workflow-controller:v3.3.10

FROM $ARGO_GOLANG AS build
WORKDIR /src
# Pin the official 3.3.10 source; only the TaskResult event handler is backported.
RUN git init && git remote add origin https://github.com/argoproj/argo-workflows.git \
    && git fetch --depth=1 origin b19870d737a14b21d86f6267642a63dd14e5acd5 \
    && git checkout --detach FETCH_HEAD
COPY controller/taskresult.patch /tmp/taskresult.patch
RUN git apply --check /tmp/taskresult.patch && git apply /tmp/taskresult.patch
COPY controller/taskresult_progress_test.go workflow/controller/taskresult_progress_test.go
ENV CGO_ENABLED=0 GOMAXPROCS=2
RUN go test -p 1 ./workflow/controller -run '^TestTaskResultProgressEnqueuesWorkflow$' -count=1
RUN go build -p 1 -trimpath \
    -ldflags '-s -w -X github.com/argoproj/argo-workflows/v3.version=v3.3.10-ch.1 -X github.com/argoproj/argo-workflows/v3.gitCommit=b19870d737a14b21d86f6267642a63dd14e5acd5 -X github.com/argoproj/argo-workflows/v3.gitTreeState=dirty' \
    -o /out/workflow-controller ./cmd/workflow-controller

FROM $ARGO_CONTROLLER
COPY --from=build --chown=8737 /out/workflow-controller /bin/workflow-controller
