import * as puppeteer from "puppeteer";

let page: any;
let browser: any;


describe("Sandbox", () => {
  console.log(process.env);
  if (!process.env.SKIP_SMOKETEST) {
    
    beforeAll(async () => {
      browser = await puppeteer.launch({ args: ['--no-sandbox'], headless: !process.env.PUPPETEER_DISPLAY, })

      page = await browser.newPage();
      page.on('pageerror', ({ message }: any) => {
        throw new Error("Page error -- " + message)
      }
      )
        .on('response', (response: any) => {
          if (!process.env.IGNORE_REQUEST_ERRORS) {
            if (response.status() >= 400) {
              console.log(`${response.status()} ${response.url()}`)
            }
            expect(response.status()).toBeLessThan(400)
          }
        })

        .on('requestfailed', (request: any) => {

          console.warn(`${request.failure().errorText} ${request.url()}`);
          if (!process.env.IGNORE_REQUEST_ERRORS) {
            throw new Error("Request failure -- " + request.failure().errorText);
          }
        })



      page.on('console', (msg: puppeteer.ConsoleMessage) => {

        if (!process.env.IGNORE_CONSOLE_ERRORS) {
          if (msg.type().includes("err")) {
            console.warn(msg);
            throw new Error("Console error -- " + msg.text())
          }
        }
      }
      );

      console.log("Checking page", process.env.APP_URL)
      await page
        .goto(process.env.APP_URL, {
          waitUntil: "networkidle0",
        })
        .catch(() => { });

      if (page.url().includes("accounts.") && process.env.USERNAME && process.env.PASSWORD) {
        console.log("Attempting login on", page.url())
        await page.type("#username", process.env.USERNAME);
        await page.type("#password", process.env.PASSWORD);
        await page.keyboard.press("Enter");
      }

    });
    afterAll(() => {
      if (!page.isClosed()) {
        browser.close();
      }
    });

    test("Check page", async () => {
      await page.waitForSelector("body");

    });
  } else {
    test("Skip Smoke test", async () => {


    });
  }




});

