# Common API microservice

The common microservice is intended to provide utility information about the 
deployment and its configuration to the frontends.

## Functionality
The main functionalities of the common microservice are:
- Information about the current version/build
- Accounts endpoint and configuration information
- Sentry endpoint

## How to use it in your application

First of all, have to configure your application deployment to include
the common microservice on the dependencies and used services.

`myapp/deploy/values.yaml`
```yaml
harness:
  ...
  dependencies:
    soft:
      - common
      ...
    ...
  use_services:
  - name: common
```

The common api will be available at `/proxy/common/api` path from your app

> the `use_services` sets up the reverse proxy in your app subdomain
> to avoid cross-origin requests from the frontend

See a usage example [here](../applications/samples/frontend/src/components/Version.tsx).


