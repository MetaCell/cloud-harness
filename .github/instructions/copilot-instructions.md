# Cloud Harness

Cloud Harness provides software infrastructure and tools for neuroscience data computing and analysis in a monorepo.

## General concepts

### Files content

- `applications`: Cloud Harness custom server applications go here
- `client`: Cloud Harness generated client api
- `deployment`: deployment related scripts and files
- `deployment-configuration`: deployment customization files
- `infrastructure`: infrastructure utilities
- `libraries`: Cloud Harness shared libraries
- `docs`: developers documentation files
- `tools`: Cloud Harness CLI and other tools
- `test`: Cloud Harness test utilities and test code

Verify which application/components is in scope and read specific prompt instruction before proceeding.

Check best practices in every instruction file in scope and docs and apply them when writing code or performing code reviews.
Use reference for any questions regarding project structure, development workflow, and best practices. 
If you have any doubts about where to find information, ask for clarification before proceeding.

### Development principles
- Follow the best practices and coding style guidelines outlined in the documentation and instruction files.
- Configuration is set on values.yaml files and injected into the application via Helm templates and Kubernetes manifests. Do not hardcode configuration values directly into the application code or templates.
- Structured configuration can be injected via resources, that are process by helm templates and loaded as ConfigMaps automatically. See for instance `applications/accounts/deploy/resources/realm.json`
- The cloud harness configuration API is handled by the models library and defined as [openapi spec](../../libraries/models/api/openapi.yaml). Use `harness-generate models` to generate the models library after making changes to the spec.