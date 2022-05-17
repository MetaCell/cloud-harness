import * as puppeteer from "puppeteer";

let page: any;
let browser: any;

describe("Sandbox", () => {
  beforeAll(async () => {
    browser = await puppeteer.launch({ args: ['--no-sandbox'], })

    page = await browser.newPage();
    page.on('pageerror', ({ message }: any) => expect(message).toBe(""))
      .on('response', (response: any) => {
        if (response.status() >= 400) {
          console.log(`${response.status()} ${response.url()}`)
        }
        expect(response.status()).toBeLessThan(400)
      })

      .on('requestfailed', (request: any) => {
        console.log(`${request.failure().errorText} ${request.url()}`);
        expect(request.failure().errorText).toBe("")
      })
    await page
      .goto(process.env.APP_URL || "https://github.com/MetaCell/cloud-harness/wiki/Get-Started", {
        waitUntil: "networkidle0",
      })
      // tslint:disable-next-line:no-empty
      .catch(() => { });
  });

  afterAll(() => {
    if (!page.isClosed()) {
      browser.close();
    }
  });

  test("Check page", async () => {

    await page.waitForSelector("body");

  });
});
