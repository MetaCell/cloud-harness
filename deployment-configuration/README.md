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

