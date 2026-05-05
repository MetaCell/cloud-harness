# Deployment CLI Tools

## Environment

- Activate `conda activate ch` before any backend command.
- Use pip (inside `ch`) for backend dependencies; Yarn for any frontend work.

## Key Scripts

- `harness-generate` — generate code
- `harness-deployment` — generate deployment files (Helm charts, CI/CD files, etc.)
- `harness-application` — generate application code (e.g. Django apps)
- `harness-migrate` — migration helper
- `ch_cli_tools` — Python package for deployment and other tools
- `tests/` — unit test utilities

## Code Style

Follow the project-wide style in the root [CLAUDE.md](../../CLAUDE.md). Key points for this package:

- Keep architecture lean — avoid unnecessary layers and abstractions.
- Utils: stateless pure functions, no ORM or external data sources.
- Helpers: stateless business logic pieces.
- Services: business workflows and cross-model coordination.
- Bubble exceptions up; never swallow them silently in helpers or services.
- Cover critical logic with unit tests using mocks to isolate units.

## Constraints

- Never start development servers.
- Never create documentation files unless explicitly asked.
- Always use pip inside `ch` conda env; never use npm.
