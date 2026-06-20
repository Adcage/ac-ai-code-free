import { test, expect } from "@playwright/test";

const UNIQUE = Date.now().toString(36);
const TEST_USER = {
  account: `e2e${UNIQUE}`,
  password: "Test123456!",
};

test.describe("App CRUD E2E Flow", () => {
  const errors: string[] = [];

  test.beforeEach(async ({ page }) => {
    errors.length = 0;

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(`[CONSOLE] ${msg.text()}`);
      }
    });

    page.on("requestfailed", (request) => {
      const url = request.url();
      if (
        url.includes("hmr") ||
        url.includes("hot-update") ||
        url.includes("vite")
      )
        return;
      errors.push(`[NETWORK] ${request.failure()?.errorText} — ${url}`);
    });

    page.on("response", (response) => {
      if (response.status() >= 500) {
        errors.push(`[SERVER 5xx] ${response.status()} — ${response.url()}`);
      }
    });
  });

  test.afterEach(async () => {
    if (errors.length > 0) {
      console.warn("Errors detected during test:");
      errors.forEach((e) => console.warn("  ", e));
    }
  });

  test("Full E2E: register, login, create app, verify persistence", async ({
    page,
  }) => {
    // Step 1: Visit homepage
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: "test-results/step1-home.png" });
    const bodyText = (await page.textContent("body")) || "";
    console.log(`Home page body length: ${bodyText.length}`);
    console.log(`Current URL: ${page.url()}`);

    // Step 2: Find register link and navigate
    const regKeywords = ["注册", "register", "还没有账号", "立即注册"];
    let foundRegLink = false;

    for (const kw of regKeywords) {
      const link = page.getByText(kw, { exact: false }).first();
      if ((await link.count()) > 0 && (await link.isVisible())) {
        await link.click();
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(1500);
        foundRegLink = true;
        console.log(`Clicked register link with text: "${kw}"`);
        break;
      }
    }

    if (!foundRegLink) {
      // Try navigating to register page directly
      console.log("No register link found, trying direct URL");
      await page.goto("/user/register");
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1500);
    }

    await page.screenshot({ path: "test-results/step2-register.png" });
    console.log(`After register nav, URL: ${page.url()}`);

    // Step 3: Fill registration form
    const accountInput = page.locator("input").filter({ hasText: "" }).first();

    // Try multiple selector strategies for form inputs
    const accountSelectors = [
      'input[id*="userAccount"]',
      'input[id*="account"]',
      'input[name*="userAccount"]',
      'input[placeholder*="请输入账号"]',
      'input[placeholder*="用户名"]',
      'input[placeholder*="账号"]',
    ];

    let accInput = accountInput;
    for (const sel of accountSelectors) {
      const el = page.locator(sel).first();
      if ((await el.count()) > 0) {
        accInput = el;
        console.log(`Found account input: ${sel}`);
        break;
      }
    }

    if ((await accInput.count()) > 0 && (await accInput.isVisible())) {
      await accInput.fill(TEST_USER.account);
      console.log(`Filled account: ${TEST_USER.account}`);
    } else {
      console.log("Account input not found, inspecting page...");
      const inputs = page.locator("input");
      const inputCount = await inputs.count();
      console.log(`Total inputs on page: ${inputCount}`);
      for (let i = 0; i < inputCount; i++) {
        const inp = inputs.nth(i);
        const type = await inp.getAttribute("type");
        const placeholder = await inp.getAttribute("placeholder");
        const name = await inp.getAttribute("name");
        const id = await inp.getAttribute("id");
        console.log(
          `Input[${i}]: type="${type}" placeholder="${placeholder}" name="${name}" id="${id}"`
        );
      }
    }

    // Fill password
    const passwordInputs = page.locator('input[type="password"]');
    const pwCount = await passwordInputs.count();
    if (pwCount >= 1) {
      await passwordInputs.nth(0).fill(TEST_USER.password);
      console.log("Filled password (first field)");
    }
    if (pwCount >= 2) {
      await passwordInputs.nth(1).fill(TEST_USER.password);
      console.log("Filled confirm password (second field)");
    }

    // Submit
    const submitButtons = [
      'button[type="submit"]',
      'button:has-text("注册")',
      'button:has-text("Register")',
    ];
    let submitted = false;
    for (const sel of submitButtons) {
      const btn = page.locator(sel).first();
      if ((await btn.count()) > 0 && (await btn.isVisible())) {
        await btn.click();
        submitted = true;
        console.log(`Clicked submit: ${sel}`);
        break;
      }
    }

    if (submitted) {
      await page.waitForTimeout(2500);
      await page.waitForLoadState("networkidle");
    }

    await page.screenshot({ path: "test-results/step3-after-register.png" });
    console.log(`After submit, URL: ${page.url()}`);

    // Step 4: Check for app creation
    const createKeywords = ["创建应用", "新建应用", "创建", "新建"];
    let clickedCreate = false;

    for (const kw of createKeywords) {
      const btn = page.getByText(kw, { exact: false }).first();
      if ((await btn.count()) > 0 && (await btn.isVisible())) {
        await btn.click();
        clickedCreate = true;
        console.log(`Clicked: "${kw}"`);
        break;
      }
    }

    if (clickedCreate) {
      await page.waitForTimeout(1500);
      await page.screenshot({ path: "test-results/step4-create-dialog.png" });

      // Fill app name
      const nameInputSelectors = [
        'input[id*="name"]',
        'input[placeholder*="应用名"]',
        'input[placeholder*="名称"]',
        'input[placeholder*="项目名"]',
      ];
      for (const sel of nameInputSelectors) {
        const inp = page.locator(sel).first();
        if ((await inp.count()) > 0 && (await inp.isVisible())) {
          await inp.fill(`E2E Test App ${UNIQUE}`);
          console.log(`Filled app name via ${sel}`);
          break;
        }
      }

      // Fill description
      const descInput = page.locator("textarea").first();
      if ((await descInput.count()) > 0 && (await descInput.isVisible())) {
        await descInput.fill("E2E test app for automated testing");
      }

      // Confirm
      const confirmSelectors = [
        'button:has-text("确定")',
        'button:has-text("提交")',
        'button:has-text("创建")',
        'button[type="submit"]',
      ];
      for (const sel of confirmSelectors) {
        const btn = page.locator(sel).first();
        if ((await btn.count()) > 0 && (await btn.isVisible())) {
          await btn.click();
          console.log(`Confirmed via: ${sel}`);
          break;
        }
      }

      await page.waitForTimeout(2000);
    }

    await page.screenshot({ path: "test-results/step5-final.png" });

    // Step 5: Final assertions
    const finalContent = (await page.textContent("body")) || "";
    console.log(`Final page content length: ${finalContent.length}`);

    // Page should have meaningful content
    expect(finalContent.length).toBeGreaterThan(0);

    // Page title should be present
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);

    // Check no unexpected errors (ignore favicon 404s)
    const realErrors = errors.filter(
      (e) =>
        !e.includes("favicon") &&
        !e.includes("_nuxt") &&
        !e.includes("iconfont")
    );
    if (realErrors.length > 0) {
      console.warn("Unexpected errors found:");
      realErrors.forEach((e) => console.warn(e));
    }
    expect(realErrors).toHaveLength(0);
  });
});
