# Default deployment templates

Templates used to personalize the automatic infrastructure definition.

Those files are used by the script `harness-deployment` script.

- `values-template.yaml`: base for `helm/values.yaml`. Modify this file to add values related to new infrastructure
  elements not defined as a CloudHarness application (e.g. a new database)
- `value-template.yaml`: base for cloudharness application configuration inside `values.yaml`. Prefer adding a
  custom `values.yaml` to your application over changing this file.
- `codefresh-template-[dev|prod].yaml`: base for `codefresh/codefresh-[dev|prod].yaml`. Modify this file if you want to
  change the build steps inside codefresh
- `codefresh-build-template.yaml`: base for a single build entry in `codefresh.yaml`
- `codefresh-publish-template.yaml`: base for a single publish (image tagging) entry in `codefresh.yaml`

## Generating HELM Chart documentation

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