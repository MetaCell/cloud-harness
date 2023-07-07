//IMPORTS:
const puppeteer = require("puppeteer");
const path = require("path");
var scriptName = path.basename(__filename, ".js");
const selectors = require("./selectors");

const antibody_type = require("./submissions.json");

//PAGE INFO:
const baseURL = process.env.APP_URL || "https://www.areg.dev.metacell.us/";
const PAGE_WAIT = 3000;
const TIMEOUT = 10000;


//USERS:
const USERNAME = "metacell-qa";
const PASSWORD = "test";

function range(size, startAt = 0) {
  return Array.from({ length: size }, (_, i) => i + startAt);
}

//TESTS:

jest.setTimeout(300000);

let page;
let browser;

async function click(selector) {
  const element = await page.$(selector);
  const value = await element.evaluate((el) => el.click());
  return value;
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

describe("E2E Flow for AntiBody Registry", () => {
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

    await page.waitForSelector(selectors.NAME_ID_FIELD);

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


  it("Log In", async () => {
    console.log("Logging in ...");

    click(selectors.LOGIN_BUTTON)

    await page.waitForSelector(selectors.KC_USERNAME, { hidden: false });
    expect(page.url()).toContain("accounts");

    await page.type(
      selectors.KC_USERNAME,
      process.env.username || USERNAME
    );

    await page.type(
      selectors.KC_PASSWORD,
      process.env.password || PASSWORD
    );


    await page.click(selectors.KC_LOGIN_BUTTON);

    await page.waitForSelector(selectors.MY_SUBMISSIONS);

    await page.waitForSelector(selectors.USER_MENU);

    console.log("User logged in");
  });

  it("Submit a Commercial AntiBody", async () => {
    console.log("Submitting Commercial Antibody ...");

    await page.waitForSelector(selectors.ADD_SUBMISSION);
    await page.click(selectors.ADD_SUBMISSION);

    expect(page.url()).toContain("/add");

    await page.waitForSelector(selectors.SUBMISSION_PROGRESS_BAR);

    await page.click(selectors.NEXT_BUTTON);

    await page.waitForSelector(selectors.INPUT_URL);

    await page.type(
      selectors.INPUT_URL,
      antibody_type.commercial.vendor_product_page
    );

    await page.waitForSelector(selectors.SUBMIT, { disabled: true });

    const catalogNumber = Math.floor(100000 + Math.random() * 900000);

    await page.type(
      selectors.INPUT_CATALOG_NUMBER,
      String(catalogNumber)
    );

    await page.waitForSelector(
      `iframe[src="${antibody_type.commercial.vendor_product_page}"]`
    );

    await page.type(
      selectors.INPUT_VENDOR,
      antibody_type.commercial.vendor
    );


    await page.waitForSelector(selectors.SUBMIT, { disabled: false });

    await page.type(
      selectors.INPUT_NAME,
      antibody_type.commercial.antibody_name
    );
    await page.waitForSelector(selectors.INPUT_HOST);

    await page.type(
      selectors.INPUT_HOST,
      antibody_type.commercial.host_species
    );
    await page.waitForSelector(selectors.INPUT_TARGET_SPECIES);

    await page.type(
      selectors.INPUT_TARGET_SPECIES,
      antibody_type.commercial.target_reactive_species
    );
    await page.waitForSelector(selectors.INPUT_ANTIBODY_TARGET);

    await page.type(
      selectors.INPUT_ANTIBODY_TARGET,
      antibody_type.commercial.antibody_target
    );
    await page.waitForSelector(selectors.CLONALITY);

    await page.click(selectors.CLONALITY);
    await page.waitForSelector(selectors.CLONALITY_OPTIONS);
    await page.click(selectors.RECOMBINANT_CLONALITY);
    await page.waitForSelector(selectors.INPUT_CLONE_ID);

    await page.type(
      selectors.INPUT_CLONE_ID,
      antibody_type.commercial.clone_id
    );
    await page.waitForSelector(selectors.INPUT_ISOTYPE);

    await page.type(
      selectors.INPUT_ISOTYPE,
      antibody_type.commercial.isotype
    );
    await page.waitForSelector(selectors.INPUT_CONJUGATE);

    await page.type(
      selectors.INPUT_CONJUGATE,
      antibody_type.commercial.conjugate
    );
    await page.waitForSelector(selectors.INPUT_FORMAT);

    await page.type(
      selectors.INPUT_FORMAT,
      antibody_type.commercial.antibody_format
    );
    await page.waitForSelector(selectors.INPUT_UNIPROT_ID);

    await page.type(
      selectors.INPUT_UNIPROT_ID,
      antibody_type.commercial.uniprot_id
    );
    await page.waitForSelector(selectors.INPUT_EPITOPE);

    await page.type(
      selectors.INPUT_EPITOPE,
      antibody_type.commercial.epitope
    );
    await page.waitForSelector(selectors.INPUT_APPLICATIONS);

    await page.type(
      selectors.INPUT_APPLICATIONS,
      antibody_type.commercial.applications
    );
    await page.waitForSelector(selectors.INPUT_COMMENTS);

    await page.type(
      selectors.INPUT_COMMENTS,
      antibody_type.commercial.comments
    );
    await page.waitForSelector(selectors.SUBMIT);

    await page.click(selectors.SUBMIT);

    await page.waitForSelector(selectors.SUCCESSFUL_SUBMISSION);
    await page.waitForSelector(selectors.CLOSE_SUBMISSION);
    await page.click(selectors.CLOSE_SUBMISSION);

    await page.waitForSelector(selectors.TABLE);
    await page.waitForSelector(selectors.NAME_ID_FIELD);

    console.log("Antibody submitted successfully");
  });

  it("Submit a Personal AntiBody", async () => {
    console.log("Submitting Personal Antibody ...");

    await page.waitForSelector(selectors.ADD_SUBMISSION);
    await page.click(selectors.ADD_SUBMISSION);  

    await page.waitForSelector(selectors.SUBMISSION_PROGRESS_BAR);
    expect(page.url()).toContain("/add");
    await page.waitForSelector(selectors.ANTIBODY_TYPE);

    const antibody_type_buttons = await page.$$(
      "button.MuiCardActionArea-root"
    );
    for (var i = 0; i < antibody_type_buttons.length; i++) {
      await antibody_type_buttons[1].click();
    }

    await page.click(selectors.NEXT_BUTTON);

    await page.waitForSelector(selectors.INPUT_CATALOG_NUMBER);

    await page.waitForSelector(selectors.SUBMIT, { disabled: true });

    const catalogNumber = Math.floor(100000 + Math.random() * 900000);
    await page.type(
      selectors.INPUT_CATALOG_NUMBER,
      String(catalogNumber)
    );
    await page.waitForSelector(selectors.INPUT_VENDOR);

    await page.type(
      selectors.INPUT_VENDOR,
      antibody_type.personal.vendor
    );
    await page.waitForSelector(selectors.INPUT_URL);

    await page.type(
      selectors.INPUT_URL,
      antibody_type.personal.vendor_product_page
    );
    await page.waitForSelector(selectors.INPUT_NAME);

    await page.type(
      selectors.INPUT_NAME,
      antibody_type.personal.antibody_name
    );
    await page.waitForSelector(selectors.INPUT_NAME);

    await page.type(
      selectors.INPUT_HOST,
      antibody_type.personal.host_species
    );
    await page.waitForSelector(selectors.INPUT_HOST);

    await page.type(
      selectors.INPUT_TARGET_SPECIES,
      antibody_type.personal.target_reactive_species
    );
    await page.waitForSelector(selectors.INPUT_TARGET_SPECIES);

    await page.type(
      selectors.INPUT_ANTIBODY_TARGET,
      antibody_type.personal.antibody_target
    );
    await page.waitForSelector(selectors.CLONALITY);

    await page.click(selectors.CLONALITY);
    await page.waitForSelector(selectors.CLONALITY_OPTIONS);
    await page.click(selectors.RECOMBINANT_CLONALITY);
    await page.waitForSelector(selectors.INPUT_CLONE_ID);

    await page.type(
      selectors.INPUT_CLONE_ID,
      antibody_type.personal.clone_id
    );

    await page.waitForSelector(selectors.SUBMIT, { disabled: false });

    await page.type(
      selectors.INPUT_ISOTYPE,
      antibody_type.personal.isotype
    );
    await page.waitForSelector(selectors.INPUT_CONJUGATE);

    await page.type(
      selectors.INPUT_CONJUGATE,
      antibody_type.personal.conjugate
    );
    await page.waitForSelector(selectors.INPUT_FORMAT);

    await page.type(
      selectors.INPUT_FORMAT,
      antibody_type.personal.antibody_format
    );
    await page.waitForSelector(selectors.INPUT_UNIPROT_ID);

    await page.type(
      selectors.INPUT_UNIPROT_ID,
      antibody_type.personal.uniprot_id
    );
    await page.waitForSelector(selectors.INPUT_EPITOPE);

    await page.type(
      selectors.INPUT_EPITOPE,
      antibody_type.personal.epitope
    );
    await page.waitForSelector(selectors.INPUT_APPLICATIONS);

    await page.type(
      selectors.INPUT_APPLICATIONS,
      antibody_type.personal.applications
    );
    await page.waitForSelector(selectors.INPUT_CITATION);

    await page.type(
      selectors.INPUT_CITATION,
      antibody_type.personal.citation
    );
    await page.waitForSelector(selectors.INPUT_COMMENTS);

    await page.type(
      selectors.INPUT_COMMENTS,
      antibody_type.personal.comments
    );
    await page.waitForSelector(selectors.SUBMIT);

    await page.click(selectors.SUBMIT);

    await page.waitForSelector(selectors.SUCCESSFUL_SUBMISSION);

    await page.waitForSelector(selectors.CLOSE_SUBMISSION);
    await page.click(selectors.CLOSE_SUBMISSION);

    await page.waitForSelector(selectors.TABLE);
    await page.waitForSelector(selectors.NAME_ID_FIELD);

    console.log("Antibody submitted successfully");
  });

  it("Submit a Custom/Other AntiBody", async () => {
    console.log("Submitting Custom Antibody ...");

    await page.waitForSelector(selectors.ADD_SUBMISSION);
    await page.click(selectors.ADD_SUBMISSION);
    await page.waitForSelector(selectors.SUBMISSION_PROGRESS_BAR);
    expect(page.url()).toContain("/add");
    await page.waitForSelector(selectors.ANTIBODY_TYPE);

    const antibody_type_buttons = await page.$$(
      "button.MuiCardActionArea-root"
    );
    for (var i = 0; i < antibody_type_buttons.length; i++) {
      await antibody_type_buttons[2].click();
    }

    await page.click(selectors.NEXT_BUTTON);

    await page.waitForSelector(selectors.INPUT_CATALOG_NUMBER);

    await page.waitForSelector(selectors.SUBMIT, { disabled: true });

    const catalogNumber = Math.floor(100000 + Math.random() * 900000);
    await page.type(
      selectors.INPUT_CATALOG_NUMBER,
      String(catalogNumber)
    );
    await page.waitForSelector(selectors.INPUT_VENDOR);

    await page.type(
      selectors.INPUT_VENDOR,
      antibody_type.custom.vendor
    );
    await page.waitForSelector(selectors.INPUT_URL);

    await page.type(
      selectors.INPUT_URL,
      antibody_type.custom.vendor_product_page
    );
    await page.waitForSelector(selectors.INPUT_NAME);

    await page.type(
      selectors.INPUT_NAME,
      antibody_type.custom.antibody_name
    );
    await page.waitForSelector(selectors.INPUT_HOST);

    await page.type(
      selectors.INPUT_HOST,
      antibody_type.custom.host_species
    );
    await page.waitForSelector(selectors.INPUT_TARGET_SPECIES);

    await page.type(
      selectors.INPUT_TARGET_SPECIES,
      antibody_type.custom.target_reactive_species
    );
    await page.waitForSelector(selectors.INPUT_ANTIBODY_TARGET);

    await page.type(
      selectors.INPUT_ANTIBODY_TARGET,
      antibody_type.custom.antibody_target
    );
    await page.waitForSelector(selectors.CLONALITY);

    await page.click(selectors.CLONALITY);
    await page.waitForSelector(selectors.CLONALITY_OPTIONS);
    await page.click(selectors.RECOMBINANT_CLONALITY);
    await page.waitForSelector(selectors.INPUT_CLONE_ID);

    await page.type(
      selectors.INPUT_CLONE_ID,
      antibody_type.custom.clone_id
    );

    await page.waitForSelector(selectors.SUBMIT, { disabled: false });

    await page.type(
      selectors.INPUT_ISOTYPE,
      antibody_type.custom.isotype
    );
    await page.waitForSelector(selectors.INPUT_CONJUGATE);

    await page.type(
      selectors.INPUT_CONJUGATE,
      antibody_type.custom.conjugate
    );
    await page.waitForSelector(selectors.INPUT_FORMAT);

    await page.type(
      selectors.INPUT_FORMAT,
      antibody_type.custom.antibody_format
    );
    await page.waitForSelector(selectors.INPUT_UNIPROT_ID);

    await page.type(
      selectors.INPUT_UNIPROT_ID,
      antibody_type.custom.uniprot_id
    );
    await page.waitForSelector(selectors.INPUT_EPITOPE);

    await page.type(
      selectors.INPUT_EPITOPE,
      antibody_type.custom.epitope
    );
    await page.waitForSelector(selectors.INPUT_APPLICATIONS);

    await page.type(
      selectors.INPUT_APPLICATIONS,
      antibody_type.custom.applications
    );
    await page.waitForSelector(selectors.INPUT_CITATION);

    await page.type(
      selectors.INPUT_CITATION,
      antibody_type.custom.citation
    );
    await page.waitForSelector(selectors.INPUT_COMMENTS);

    await page.type(
      selectors.INPUT_COMMENTS,
      antibody_type.custom.comments
    );
    await page.waitForSelector(selectors.SUBMIT);

    await page.click(selectors.SUBMIT);

    await page.waitForSelector(selectors.SUCCESSFUL_SUBMISSION);

    await page.waitForSelector(selectors.CLOSE_SUBMISSION);
    await page.click(selectors.CLOSE_SUBMISSION);
    await page.waitForSelector(selectors.TABLE);
    await page.waitForSelector(selectors.NAME_ID_FIELD);

    console.log("Antibody submitted successfully");
  });

  it("Check AntiBody submissions", async () => {
    console.log("Checking Antibody submissions...");

    await page.waitForSelector(selectors.MY_SUBMISSIONS);
    click(selectors.MY_SUBMISSIONS);

    await page.waitForSelector(selectors.ANTIBODY_TARGET_FIELD);

    
    await page.click(selectors.FILTER);
    await page.waitForSelector(selectors.FILTER_TABLE);

  
    expect(ab_Target_names.find(e => e === "TWIT")).toBeTruthy();
    expect(ab_Target_names.find(e => e === "INST")).toBeTruthy();
    expect(ab_Target_names.find(e => e === "MSN")).toBeTruthy();

    console.log("Antibodies match");
  });

  it("Edit AntiBody submission", async () => {
    await page.waitForSelector(selectors.ANTIBODY_ID_FIELD);

    const ID_numbers = getValues(selectors.ANTIBODY_ID_FIELD);

    await page.click(`a[href= "/update/${ID_numbers[1]}"]`);

    await page.waitForSelector(selectors.INPUT_NAME, {
      timeout: 15000,
    });
    await page.waitForSelector(selectors.SUBMIT);

    expect(page.url()).toContain(`update/${ID_numbers[1]}`);

    await page.type(selectors.INPUT_NAME, " - Edited");

    await page.waitForSelector(selectors.SUBMIT);
    await page.click(selectors.SUBMIT);

    await page.waitForSelector(selectors.ANTIBODY_TARGET_FIELD);

    await page.click(selectors.FILTER);
    await page.waitForSelector(selectors.FILTER_TABLE);


    const nameAndIds = getValues(selectors.ANTIBODY_ID_FIELD);

    expect(nameAndIds.find(n => n.includes("Edited"))).toBeTruthy();
  });

  it("Log out", async () => {
    console.log("Logging out...");

    await page.waitForSelector(selectors.TOP_BUTTONS);

    await click('.btn-user-menu');

    await page.waitForSelector(selectors.ACCOUNT_SUBMENU);

    await click('.btn-logout');

    await page.waitForSelector(selectors.NAME_ID_FIELD);

    console.log("User logged out");
  });
});

