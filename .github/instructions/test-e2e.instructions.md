---
applyTo: "test/e2e/*"
---
# Neuroglass Research E2E Tests

## End-to-end (E2E) Tests
- **Location**: `test/e2e/*.spec.ts`
- **Framework**: Jest + Puppeteer (see existing tests for patterns)

### Login Flow
- Tests must handle the 2-step login redirect when `APP_URL` points to the accounts domain.
- Use `USERNAME` and `PASSWORD` environment variables for credentials.
- Follow the existing flow:
  - Navigate to `APP_URL` and detect redirect to accounts.
  - Enter username, submit, wait for password field, enter password, submit.
  - Wait for redirect back to the app and confirm route.

### Stability Requirements (Mandatory)
- **Waiting**: Always use Puppeteer explicit waits (`waitForSelector`, `waitForFunction`, `waitForNavigation`) with timeouts.
- **Selectors**: Rely on stable, custom selectors (see `test/e2e/selectors.ts`).
- **Do not** depend on UI copy, text content, or fragile DOM structure.
- **Avoid fixed sleeps** unless there is no deterministic signal; prefer state-based waits.
- **Resilience**: When possible, guard against flaky overlays (cookie/announcement modals).
