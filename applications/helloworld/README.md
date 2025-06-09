# HelloWorld Application

This is a minimal example demonstrating how to create a CloudHarness application.
It exposes a single endpoint returning `Hello world`.

## Local run

```bash
docker build -t helloworld .
docker run -p 8080:8080 helloworld
```

Then access `http://localhost:8080/api/hello`.

## Deploying with CloudHarness

Add this folder under `applications/` in a CloudHarness deployment or use it as a
reference for your own application repositories. Generate the helm chart with
`harness-deployment` and deploy to your Kubernetes cluster (for example AWS EKS).

For a complete project using CloudHarness, see [metacell/biotrack](https://github.com/MetaCell/biotrack).
