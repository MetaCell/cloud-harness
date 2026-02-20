---
applyTo: "tools/deployment-cli-tools/*
---
# Neuroglass Project Developer Reference

## Environment Setup

### Required Environment
- **Conda Environment Name**: `ch`
- **Python Version**: 3.12+
- **Activation Command**: `conda activate ch`

### Package Managers
- **Frontend**: Yarn (NEVER use npm)
- **Backend**: pip (within conda environment only)

### Pre-requisites Checklist
- [ ] Conda environment `ch` is activated
- [ ] Correct directory navigation completed
- [ ] Appropriate package manager selected (yarn/pip)

## Development Workflow

### Mandatory Pre-Command Steps
1. **ALWAYS** activate conda environment first: `conda activate ch`
2. Navigate to the appropriate project directory
3. Use yarn for frontend operations, pip for backend operations

## Project Structure

### Key Scripts
- `harness-generate` - Generate code
- `harness-deployment` - Generate deployment files: helm charts, ci/cd files, etc.
- `harness-application` - Generate application code (e.g., Django apps)
- `harness-migrate` - Migration helper tool
- `ch_cli_tools` - Python package for deployment and other tools
- `tests` - Unit test utilities and test code


## Code Style and best practices

Take the following best practices into account when writing code for the project adn while performing code reviews:

- Keep architecture lean: avoid unnecessary layers and abstractions.
- Use utils for stateless pure functions that don't hit external data sources nor the ORM. Utils are horizontal and can be used across the project.
- Use helpers to organize pieces of business logic; keep them stateless when possible.
- Use services for business workflows and cross-model coordination. Services are vertical on a single model or a group of related models
- Keep model logic close to the model when it represents domain rules or invariants.
- Handle exceptions only at the higher level; let lower layers raise. NEVER catch exceptions in helpers or services unless you are adding context and re-raising.
- Cover critical logic with unit tests, especially in helpers and services. Use mocks to isolate units under test.
- Prefer models classes for helpers and services to ensure data validation and clear interfaces. Use typed dicts for structured data that isn't covered by Schema classes. Use plain dicts only to represent real unstructured data. Avoid returning tuples.


## Important Constraints

### File Creation Rules
- **NEVER** create new README or documentation files unless explicitly requested
- Follow existing documentation patterns when updates are needed

### Development Server Rules
- **NEVER** run development servers
- **ALWAYS** assume servers are running
- **MUST** ask confirmation before opening browsers

### Package Management Rules
- **Frontend**: ONLY use yarn, NEVER npm
- **Backend**: ONLY use pip within conda environment
- **ALWAYS** activate `mnp` conda environment before any backend work

### CloudHarness Considerations
- Dependencies may need special handling in development environment
- Follow established patterns for CloudHarness integration

---