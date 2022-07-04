import * as puppeteer from "puppeteer";

let page: any;
let browser: any;

describe("Sandbox", () => {
  beforeAll(async () => {
    browser = await puppeteer.launch({ args: ['--no-sandbox'], headless: true, })

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
      .goto(process.env.APP_URL, {
        waitUntil: "networkidle0",
      })
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

  if (process.env.USERNAME && process.env.PASSWORD) {
    test("Login", async () => {

      page
        .on("response", (response: any) => {
        if (response.status() >= 300) {
          expect(response.status()).toBeLessThan(400);
        }
        });

      await page.type("#username", process.env.USERNAME); 
      await page.type("#password", process.env.PASSWORD); 
      await page.keyboard.press("Enter");
      await page.waitForSelector("#user-menu"); 
      await page.waitForTimeout(1000); 

    });
  }
});
