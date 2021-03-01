# Argo sub chart

TODO change this to a chart dependency whenever this is fixed: https://github.com/argoproj/argo-helm/issues/521

To use as add dependency, add the following to Chart.yaml
```
dependencies:
- name: argo
  version: ">=0.14.0"
  repository: https://argoproj.github.io/argo-helm
  condition: true
  alias: apps-argo
```
