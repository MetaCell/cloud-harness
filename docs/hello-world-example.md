# Hello World with CloudHarness

This document shows how to create and deploy a simple application using CloudHarness.
It follows the same strategy used in the [metacell/biotrack] project.

1. Place your application inside the `applications` directory or keep it in a
   separate repository and include it during deployment.
2. Generate the helm chart with `harness-deployment`.
3. Deploy the chart to your Kubernetes cluster (e.g. on AWS) and expose it with
your VPN or OAuth proxy.

The [`applications/helloworld`] folder contains a minimal Flask service returning
`Hello world`.
