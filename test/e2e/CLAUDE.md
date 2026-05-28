# E2E Tests

**Framework**: Jest + Puppeteer. Follow patterns in existing `*.spec.ts` files.

## Login Flow

Tests that point `APP_URL` at the accounts domain must handle the 2-step login redirect:

1. Navigate to `APP_URL` and detect the redirect to accounts.
2. Enter the username from `USERNAME`, submit, wait for the password field.
3. Enter the password from `PASSWORD`, submit.
4. Wait for redirect back to the app and confirm the expected route.

## Stability Requirements

- **Waits**: always use explicit Puppeteer waits (`waitForSelector`, `waitForFunction`, `waitForNavigation`) with timeouts.
- **Selectors**: use stable custom selectors from `test/e2e/selectors.ts`. Never depend on UI copy, text content, or fragile DOM structure.
- **No fixed sleeps** unless there is no deterministic signal — prefer state-based waits.
- **Resilience**: guard against flaky overlays (cookie/announcement modals) where possible.
