# Cloud Harness

Cloud Harness provides software infrastructure and tools for neuroscience data computing and analysis in a monorepo.

## Repository Layout

- `applications/` — Cloud Harness custom server applications
- `client/` — generated client API
- `deployment/` — deployment-related scripts and files
- `deployment-configuration/` — deployment customization files
- `infrastructure/` — infrastructure utilities
- `libraries/` — Cloud Harness shared libraries
- `docs/` — developer documentation
- `tools/` — Cloud Harness CLI and other tools
- `test/` — test utilities and test code

Before working on a task, identify which application/component is in scope and read any `CLAUDE.md` inside that subtree.

## Environment Setup

- **Conda environment**: `ch` (Python 3.12+) — activate with `conda activate ch`
- **Frontend package manager**: Yarn — **never** use npm
- **Backend package manager**: pip — only inside the conda environment

Always activate `conda activate ch` before any backend command.

## Development Principles

- Configuration lives in `values.yaml` files and is injected via Helm templates and Kubernetes manifests. Never hardcode configuration in application code or templates.
- Structured configuration can be injected via resources processed by Helm templates and loaded as ConfigMaps automatically (e.g. `applications/accounts/deploy/resources/realm.json`).
- The Cloud Harness configuration API is defined as an [OpenAPI spec](libraries/models/api/openapi.yaml). Run `harness-generate models` after changing the spec.

## Code Style

- Keep architecture lean — avoid unnecessary layers and abstractions.
- Use **utils** for stateless pure functions that don't touch external data sources or the ORM.
- Use **helpers** for pieces of business logic; keep them stateless when possible.
- Use **services** for business workflows and cross-model coordination.
- Keep model logic close to the model when it represents domain rules or invariants.
- Handle exceptions only at the highest level; let lower layers raise. Never catch in helpers or services unless adding context and re-raising.
- Cover critical logic with unit tests, especially helpers and services. Use mocks to isolate units.
- Prefer model classes for helpers and services. Use typed dicts for structured data not covered by schema classes. Use plain dicts only for genuinely unstructured data. Avoid returning tuples.
- Bubble exceptions up to where they can be handled. Avoid return-value error signalling. Wrap library and untyped exceptions in custom exceptions with clear meaning.

## Important Constraints

- **Never** create README or documentation files unless explicitly requested.
- **Never** start development servers — assume they are already running.
- **Always** ask before opening a browser.
- **Frontend**: Yarn only. **Backend**: pip inside the `ch` conda environment only.


# Using Cloudharness CLI Tools

## Environment
- Activate `conda activate ch` before any backend command.
- Run `sh install.sh` to install cli tools

## Key Scripts

- `harness-generate` — generate code
- `harness-deployment` — generate deployment files (Helm charts, CI/CD files, etc.)
- `harness-application` — generate application code (e.g. Django apps)
- `harness-migrate` — migration helper
- `ch_cli_tools` — Python package for deployment and other tools
- `tests/` — unit test utilities
