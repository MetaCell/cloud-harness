import * as puppeteer from "puppeteer";

let page: any;
let browser: any;

describe("End to end test", () => {
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

  // TODO CHANGEME
  test("should see the landing page", async () => {
    await page.waitForSelector("h1");
    const title = await page.$eval("h1", (el: { textContent: any }) => {
      return el.textContent;
    });

    expect(await page.title()).toEqual("Samples");
    expect(title).toEqual("Sample React application is working!");
  });
});
