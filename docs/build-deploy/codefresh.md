# Continuous deployment with Codefresh

Codefresh pipelines are generated as `deployment/codefresh-[ENV].yaml`.
These files can be loaded from codefresh as documented [here](https://codefresh.io/docs/docs/configure-ci-cd-pipeline/pipelines/).

The pipeline will take care of building the images from the source code and deploy the helm chart.
Log in to codefresh and run the pipeline associated to the repository.

- To setup a new dev pipeline, indicate the remote yaml path `./deployment/codefresh-dev.yaml`
- To setup a new production pipeline, indicate the remote yaml path `./deployment/codefresh-prod.yaml`

In order to update the deployment, run
```
harness-deployment . -e [ENV]
```

