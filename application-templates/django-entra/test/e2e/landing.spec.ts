/**
 * End to end tests, authenticated with test tokens (as the API tests, see test/api/entra_token.py).
 *
 * Requires ENTRA_TEST_PRIVATE_KEY and a deployment with `entra.test_tokens: true` (deploy/values-test.yaml).
 * The tenant and client ids are read from ENTRA_TENANT_ID and ENTRA_CLIENT_ID, or from deploy/values.yaml
 * when the application folder is available (local runs with harness-test).
 *
 * The browser sends the token in the Authorization header of every request to the application,
 * so it is logged in without going through the Entra sign-in page.
 * The common CloudHarness smoke test cannot log in: it is disabled in the test values and
 * its checks (no console errors, no failed requests) are done here instead.
 */
import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";
import * as puppeteer from "puppeteer";

const TEST_KEY_ID = "cloudharness-test";
const USER_ROLE = "__APP_NAME__-user";

const APP_URL = (process.env.APP_URL || "").replace(/\/$/, "");
const APP_ORIGIN = new URL(APP_URL).origin;

function entraValue(key: string): string | undefined {
  // only the entra section of deploy/values.yaml defines tenant_id and client_id
  const valuesPath = path.join(__dirname, "..", "..", "deploy", "values.yaml");
  if (!fs.existsSync(valuesPath)) {
    return undefined;
  }
  const match = fs.readFileSync(valuesPath, "utf8").match(new RegExp(`^\\s+${key}:\\s*"?([^"\\s#]+)"?`, "m"));
  return match ? match[1] : undefined;
}

function base64url(data: string | Buffer): string {
  return Buffer.from(data).toString("base64").replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
}

// RFC 4122 version 5 UUID, the same as Python's uuid.uuid5(uuid.NAMESPACE_DNS, name):
// the tests reuse the same Django user as the API tests
function uuid5(name: string): string {
  const namespaceDns = Buffer.from("6ba7b8109dad11d180b400c04fd430c8", "hex");
  const hash = crypto.createHash("sha1").update(Buffer.concat([namespaceDns, Buffer.from(name)])).digest();
  hash[6] = (hash[6] & 0x0f) | 0x50;
  hash[8] = (hash[8] & 0x3f) | 0x80;
  const hex = hash.slice(0, 16).toString("hex");
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join("-");
}

function createToken(roles: string[], username: string, name: string): string {
  const privateKey = process.env.ENTRA_TEST_PRIVATE_KEY;
  const tenantId = process.env.ENTRA_TENANT_ID || entraValue("tenant_id");
  const clientId = process.env.ENTRA_CLIENT_ID || entraValue("client_id");
  if (!privateKey || !tenantId || !clientId) {
    throw new Error("Set ENTRA_TEST_PRIVATE_KEY, and ENTRA_TENANT_ID and ENTRA_CLIENT_ID (or entra in deploy/values.yaml)");
  }
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT", kid: TEST_KEY_ID };
  const claims = {
    iss: `https://login.microsoftonline.com/${tenantId}/v2.0`,
    aud: `api://${clientId}`,
    tid: tenantId,
    oid: uuid5(username),
    preferred_username: username,
    name,
    roles,
    // a delegated access token for the API scope
    scp: "access",
    iat: now,
    exp: now + 3600,
  };
  const unsigned = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(claims))}`;
  const signature = crypto.createSign("RSA-SHA256").update(unsigned).sign(privateKey);
  return `${unsigned}.${base64url(signature)}`;
}

async function openPage(browser: puppeteer.Browser, token?: string) {
  const page = await browser.newPage();
  const errors: string[] = [];
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    // the token goes to the application only, never to third party origins
    if (token && new URL(request.url()).origin === APP_ORIGIN) {
      request.continue({ headers: { ...request.headers(), Authorization: `Bearer ${token}` } });
    } else {
      request.continue();
    }
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(`console: ${msg.text()}`);
    }
  });
  page.on("pageerror", (error) => errors.push(`page: ${error}`));
  page.on("response", (response) => {
    if (response.status() >= 400 && new URL(response.url()).origin === APP_ORIGIN) {
      errors.push(`${response.status()} ${response.url()}`);
    }
  });
  return { page, errors };
}

describe("End to end test", () => {
  let browser: puppeteer.Browser;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      args: ["--no-sandbox"],
      headless: !process.env.PUPPETEER_DISPLAY,
      // local deployments use self-signed certificates
      acceptInsecureCerts: true,
    });
  });

  afterAll(async () => {
    await browser.close();
  });

  test("a user with an app role sees the landing page", async () => {
    const token = createToken([USER_ROLE], "test-e2e-user@example.com", "Test E2e");
    const { page, errors } = await openPage(browser, token);
    await page.goto(APP_URL, { waitUntil: "networkidle0" });

    expect(new URL(page.url()).origin).toBe(APP_ORIGIN);
    await page.waitForSelector("h1");
    expect(await page.$eval("h1", (el) => el.textContent)).toBeTruthy();

    // the frontend loaded the current user from /api/me
    await page.waitForFunction(() => document.body.innerText.includes("Logged in as"));
    const body = await page.evaluate(() => document.body.innerText);
    expect(body).toContain("test-e2e-user@example.com");
    expect(body).toContain(USER_ROLE);

    expect(errors).toEqual([]);
    await page.close();
  });

  test("a user without an app role is forbidden", async () => {
    const token = createToken([], "test-e2e-norole@example.com", "Test Norole");
    const { page } = await openPage(browser, token);
    const response = await page.goto(APP_URL, { waitUntil: "domcontentloaded" });

    expect(response && response.status()).toBe(403);
    await page.close();
  });

  test("an anonymous user is sent to the Entra login", async () => {
    const { page } = await openPage(browser);
    // stop at the application redirect, without loading the Microsoft sign-in page
    const responses: puppeteer.HTTPResponse[] = [];
    page.on("response", (response) => responses.push(response));
    await page.goto(APP_URL, { waitUntil: "domcontentloaded" }).catch(() => {});

    const first = responses.find((response) => new URL(response.url()).origin === APP_ORIGIN);
    expect(first && first.status()).toBe(302);
    expect(first && first.headers()["location"]).toContain("/oidc/login/");
    await page.close();
  });
});
