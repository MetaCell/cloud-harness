//IMPORTS:
const puppeteer = require("puppeteer");
const path = require("path");
var scriptName = path.basename(__filename, ".js");
const s = require("./selectors");


//PAGE INFO:
const baseURL = process.env.APP_URL || "https://www.areg.dev.metacell.us/";
const PAGE_WAIT = 3000;
const TIMEOUT = 1000;


function range(size, startAt = 0) {
  return Array.from({ length: size }, (_, i) => i + startAt);
}

//TESTS:

jest.setTimeout(300000);

let page;
let browser;



async function waitLoaderToDisappear() {
  try {
    await page.waitForSelector(s.PROGRESS_LOADER, { timeout: TIMEOUT });
  } catch(e) {
    console.log("No loader found");
  }
  try {
    await page.waitForSelector(s.CATALOG_NUMBER_FIELD, { timeout: TIMEOUT });
  } catch(e) {
    console.log("No table results found");
  }
  
}

async function getValue(selector) {
  const element = await page.$(selector);
  const value = await page.evaluate((el) => el.innerText, element);
  return value;
}

async function getValues(selector) {
  const elements = await page.$$(selector);
  const values = [];
  for(const element of elements) {
    values.push(await page.evaluate(e => e.innerText, element));
  }
  return values;
}

describe("E2E Flow for AntiBody Registry", () => {

  

  async function getRecordNumber() {
    return getValue(s.RECORD_NUMBER);
  }
  
  beforeAll(async () => {
    browser = await puppeteer.launch({
      args: [
        "--no-sandbox",
        `--window-size=1600,1000`,
        "--ignore-certificate-errors",
      ],
      headless: false,
      devtools: false,
      defaultViewport: {
        width: 1600,
        height: 1000,
      },
    });

    page = await browser.newPage();
    await page.goto(baseURL);

    await waitLoaderToDisappear()

    await page.waitForSelector(s.NAME_ID_FIELD);

    page.on("response", (response) => {
      const client_server_errors = range(90, 400);
      for (let i = 0; i < client_server_errors.length; i++) {
        expect(response.status()).not.toBe(client_server_errors[i]);
      }
    });
  });

  afterAll(() => {
    browser.close();
  });

  it("HomePage check", async () => {
    console.log("Checking the homepage ...");

    await page.waitForSelector(s.DOWNLOAD_SECTION, {
      disabled: true,
    });
    await page.waitForSelector(s.HELP);
    await page.waitForSelector(s.TABLE);
    const rec_num_str = await getRecordNumber();

    expect(parseFloat(rec_num_str)).not.toBe(0);

    const update_date = await getValue(s.UPDATE_DATE);

    expect(update_date).not.toContain("Invalid Date");

    
  });

  it("Perform Search by Catalog Number", async () => {
    console.log("Performing search by Catalog Number ...");

    await page.waitForSelector(s.CATALOG_NUMBER_FIELD);
    const cat_nums = await getValues(s.CATALOG_NUMBER_FIELD);
    expect(cat_nums[0]).toBe("Cat Num");
    expect(cat_nums[1]).not.toBeNull;

    await page.click(s.SEARCH_BAR);

    await page.type(s.SEARCH_INPUT, cat_nums[1]);

    await page.keyboard.press('Enter')

    await waitLoaderToDisappear();



    const search_result = await page.$$(
      s.CATALOG_NUMBER_FIELD
    );
    expect(search_result.length).toBeGreaterThanOrEqual(2);

    const rec_num_str = await getRecordNumber();

    expect(search_result.length - 1).toBe(parseFloat(rec_num_str));

    console.log("Search successful");
  });

  it("Perform Search by other field", async () => {
    console.log("Performing search by Antibody Target ...");

    await page.waitForSelector(s.ANTIBODY_TARGET_FIELD);
    const targAntigens = await getValues(s.ANTIBODY_TARGET_FIELD);
     
    expect(targAntigens[0]).toBe("Target antigen");
    expect(targAntigens[1]).not.toBeNull;

    const inputValue = getValue(s.SEARCH_INPUT);

    await page.click(s.SEARCH_INPUT)

    for (let i = 0; i < inputValue.length; i++) {
      await page.keyboard.press("Backspace");
    }
  
    await page.keyboard.press('Enter')
    
    await page.type(s.SEARCH_INPUT, targAntigens.find(ta => ta.length > 10));

    await page.keyboard.press('Enter')

    await waitLoaderToDisappear();


    const search_result = await getValues(s.ANTIBODY_TARGET_FIELD);
    expect(search_result.length).toBeGreaterThanOrEqual(2);

    console.log("Search successful");
  });

  
});


