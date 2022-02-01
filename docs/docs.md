# Generating HELM Chart documentation

We use [helm-docs](https://github.com/norwoodj/helm-docs) to generate a markdown file containing a table of all
available parameters.

Please follow their [installation instruction](https://github.com/norwoodj/helm-docs#installation), either use `brew` on MacOS or
install from source. If you install from source, `go` is required.

`helm-docs` is able to parse yaml comments, but only if they are prefixed with `--`:

```yaml
registry:
  # -- The docker registry.
  name: "localhost:5000"
```

To generate HELM chart documentation run:

````bash
helm-docs --dry-run > docs.md
````

As a final step, update the content in the respective Cloud Harness wiki page.