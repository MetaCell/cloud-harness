import * as puppeteer from "puppeteer";

let page: any;
let browser: any;

describe("Sandbox", () => {
  beforeAll(async () => {
    browser = await puppeteer.launch({args: ['--no-sandbox'],});
    page = await browser.newPage();
    console.log(process.env.APP_URL)
    await page
      .goto(process.env.APP_URL, {
        waitUntil: "networkidle0",
      })
      // tslint:disable-next-line:no-empty
      .catch(() => {});
  });

  afterAll(() => {
    if (!page.isClosed()) {
      browser.close();
    }
  });

  test("should see the landing page", async () => {
    await page.waitForSelector("h1");
    const title = await page.$eval("h1", (el: { textContent: any }) => {
      return el.textContent;
    });

    expect(await page.title()).toEqual("CloudHarness sample application");
    expect(title).toEqual("Sample React application is working!");
  });
});
