#CloudHarness Deploy

CloudHarness Deploy is a collection of Python utilities to create CloudHarness deployments.

## harness-deployment

Generates the helm chart to deploy on Kubernetes.

Usage:

```bash
harness-deployment .
```

For more info, `harness-deployment --help`


## harness-application

Create a new REST application.

Usage:

```bash
harness-application myapp
```

For more info, `harness-application --help`

## harness-codefresh

Generates the Codefresh continuous deployment specification.

Usage:

```bash
harness-codefresh .
```

For more info, `harness-codefresh --help`

## harness-generate

Generates server and client code for all standard harness REST applications.

Usage:

```bash
harness-generate .
```

For more info, `harness-generate --help`