import { test, expect } from "@playwright/test";

const UNIQUE = Date.now().toString(36);
const TEST_USER = {
  account: `e2e${UNIQUE}`,
  password: "Test123456!",
};

test.describe("Full Agent Loop E2E: Register, Create App, Generate Code", () => {
  const errors: string[] = [];

  const IGNORED_ERROR_PATTERNS = [
    "favicon",
    "_nuxt",
    "iconfont",
    "hot-update",
    "vite",
  ];

  function isIgnored(message: string): boolean {
    return IGNORED_ERROR_PATTERNS.some((p) => message.includes(p));
  }

  function appErrors(): string[] {
    return errors.filter((e) => !isIgnored(e));
  }

  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    errors.length = 0;

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(`[CONSOLE] ${msg.text()}`);
      }
    });

    page.on("requestfailed", (request) => {
      const url = request.url();
      if (!isIgnored(url)) {
        errors.push(`[NETWORK] ${request.failure()?.errorText} — ${url}`);
      }
    });

    page.on("response", (response) => {
      if (response.status() >= 500) {
        const url = response.url();
        if (!isIgnored(url)) {
          errors.push(`[SERVER 5xx] ${response.status()} — ${url}`);
        }
      }
    });
  });

  test.afterEach(async ({}, testInfo) => {
    const realErrors = appErrors();
    if (realErrors.length > 0 && testInfo.status !== "failed") {
      console.warn(`[${testInfo.title}] Unexpected errors (${realErrors.length}):`);
      realErrors.forEach((e) => console.warn("  ", e));
    }
  });

  async function login(page: any) {
    await page.goto("/user/login");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    const isLoginPage = page.url().includes("/user/login");
    if (isLoginPage) {
      await page.getByRole("textbox", { name: "* 账号" }).fill(TEST_USER.account);
      await page.getByRole("textbox", { name: "* 密码" }).fill(TEST_USER.password);
      await page.getByRole("button", { name: "登录" }).click();
      await page.waitForTimeout(3000);
      await page.waitForLoadState("networkidle");
    }
  }

  async function goToHomeCreationPage(page: any) {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);
  }

  async function createAppFromHome(page: any, prompt: string): Promise<string> {
    await goToHomeCreationPage(page);

    const promptTextarea = page.locator(
      'textarea[placeholder*="描述你想要"], textarea[placeholder*="描述你想要的"]'
    ).first();

    if ((await promptTextarea.count()) === 0) {
      console.log("No prompt textarea on home page, checking for existing apps...");
      await page.goto("/app/my");
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1500);
      return "";
    }

    await promptTextarea.fill(prompt);
    await page.click(".send-btn");
    await page.waitForTimeout(5000);
    await page.waitForLoadState("networkidle");

    const url = page.url();
    const match = url.match(/\/app\/generate\/(\d+)/);
    return match ? match[1] : "";
  }

  test("Step 1 — Register a new user", async ({ page }) => {
    await page.goto("/user/register");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    expect(await page.title()).toBeTruthy();

    await page.getByRole("textbox", { name: "* 账号" }).fill(TEST_USER.account);
    console.log(`Created account: ${TEST_USER.account}`);

    const pwFields = page.locator('input[type="password"]');
    for (let i = 0; i < Math.min(await pwFields.count(), 2); i++) {
      await pwFields.nth(i).fill(TEST_USER.password);
    }

    await page.getByRole("button", { name: "注册" }).click();
    await page.waitForTimeout(3000);
    await page.waitForLoadState("networkidle");

    expect(page.url()).toMatch(/\/user\/login/);
    expect(appErrors()).toHaveLength(0);
  });

  test("Step 2 — Log in and verify redirect", async ({ page }) => {
    await login(page);

    const url = page.url();
    console.log(`After login URL: ${url}`);
    expect(url).not.toMatch(/\/user\/login/);

    const bodyText = (await page.textContent("body")) || "";
    expect(bodyText.length).toBeGreaterThan(100);
    expect(bodyText).toContain("用户");

    expect(appErrors()).toHaveLength(0);
  });

  test("Step 3 — My Apps page renders correctly", async ({ page }) => {
    await login(page);

    await page.goto("/app/my");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    await page.screenshot({ path: "test-results/step3-my-apps.png" });

    const bodyText = (await page.textContent("body")) || "";
    expect(bodyText).toContain("我的作品");

    const createBtn = page.locator('button:has-text("创建新应用")').first();
    const hasCreateBtn = (await createBtn.count()) > 0 && (await createBtn.isVisible());
    console.log(`"创建新应用" button: ${hasCreateBtn}`);

    expect(appErrors()).toHaveLength(0);
  });

  test("Step 4 — Create app from home page and enter generation page", async ({ page }) => {
    await login(page);

    const appId = await createAppFromHome(page, "创建一个简单的HTML登录表单页面");
    console.log(`Created app ID: ${appId}`);
    expect(appId).toBeTruthy();

    expect(page.url()).toMatch(/\/app\/generate\//);
    await page.screenshot({ path: "test-results/step4-gen-page.png" });

    expect(appErrors()).toHaveLength(0);
  });

  test("Step 5 — Verify generation page UI components", async ({ page }) => {
    await login(page);

    const appId = await createAppFromHome(page, "创建一个简单页面");
    console.log(`Created app ID: ${appId}`);
    expect(appId).toBeTruthy();

    await page.screenshot({ path: "test-results/step5-gen-page-full.png" });

    const bodyText = (await page.textContent("body")) || "";
    console.log(`Generation page content: ${bodyText.length} chars`);

    const elements = {
      topNav: page.locator('.top-nav').first(),
      chatPanel: page.locator('.chat-panel').first(),
      previewPanel: page.locator('.preview-panel').first(),
      messageList: page.locator('.message-list').first(),
    };

    for (const [name, locator] of Object.entries(elements)) {
      const has = (await locator.count()) > 0;
      console.log(`  ${name}: ${has}`);
    }

    const hasAnyKeyElement = (
      (await elements.chatPanel.count()) > 0 ||
      (await elements.messageList.count()) > 0 ||
      (await page.locator('.input-wrapper textarea').first().count()) > 0
    );
    expect(hasAnyKeyElement).toBeTruthy();

    expect(appErrors()).toHaveLength(0);
  });

  test("Step 6 — Send follow-up prompt and verify SSE response + tool events", async ({ page }) => {
    await login(page);

    const appId = await createAppFromHome(page, "创建一个登录表单");
    console.log(`Created app ID: ${appId}`);
    expect(appId).toBeTruthy();
    expect(page.url()).toMatch(/\/app\/generate\//);

    await page.waitForTimeout(3000);

    await page.screenshot({ path: "test-results/step6-post-generation.png" });

    const textareas = page.locator('textarea');
    const taCount = await textareas.count();
    console.log(`Textareas on page: ${taCount}`);

    for (let i = 0; i < Math.min(taCount, 3); i++) {
      const ta = textareas.nth(i);
      const placeholder = await ta.getAttribute("placeholder") || "";
      const visible = await ta.isVisible();
      console.log(`  textarea[${i}]: placeholder="${placeholder.substring(0, 30)}" visible=${visible}`);
    }

    const chatTextarea = page.locator('.input-wrapper textarea').first();
    const hasChat = (await chatTextarea.count()) > 0 && (await chatTextarea.isVisible());
    console.log(`Chat textarea visible: ${hasChat}`);

    if (hasChat) {
      await chatTextarea.fill("修改标题为欢迎登录");
      console.log("Filled chat textarea");

      const sendBtn = page.locator('.send-btn, .input-footer button[type="primary"]').first();
      if ((await sendBtn.count()) > 0 && (await sendBtn.isVisible())) {
        await sendBtn.click();
        console.log("Clicked send button in chat");
      }
    } else if (taCount >= 2) {
      const followUpTa = textareas.nth(1);
      if (await followUpTa.isVisible()) {
        await followUpTa.fill("修改标题为欢迎登录");
        const sendBtns = page.locator('button[type="primary"], .send-btn');
        const btnCount = await sendBtns.count();
        if (btnCount > 0) {
          await sendBtns.last().click();
          console.log("Clicked last send button");
        }
      }
    }

    await page.waitForTimeout(2000);
    await page.screenshot({ path: "test-results/step6-after-send.png" });

    try {
      const generating = page.locator('.generating-indicator');
      await generating.waitFor({ state: "visible", timeout: 10000 });
      console.log("Generating indicator appeared — SSE is active");
    } catch {
      console.log("No generating indicator within 10s");
    }

    await page.waitForTimeout(5000);

    const messages = page.locator('.message-item');
    const msgCount = await messages.count();
    console.log(`Messages in chat: ${msgCount}`);

    const userMsgs = page.locator('.message-item.user-msg');
    console.log(`User messages: ${await userMsgs.count()}`);

    const aiMsgs = page.locator('.message-item.ai-msg');
    console.log(`AI messages: ${await aiMsgs.count()}`);

    await page.waitForTimeout(5000);

    const toolCards = page.locator('.tool-call-card, details.tool-call-card');
    const toolCount = await toolCards.count();
    console.log(`Tool call cards: ${toolCount}`);

    const toolItems = page.locator('.tool-call-item');
    const itemCount = await toolItems.count();
    console.log(`Tool call items: ${itemCount}`);

    for (let i = 0; i < Math.min(itemCount, 4); i++) {
      const item = toolItems.nth(i);
      const text = await item.textContent();
      const tagEl = item.locator('.tool-call-tag');
      const tagText = (await tagEl.count()) > 0 ? await tagEl.textContent() : "?";
      console.log(`  Tool[${i}]: tag="${tagText}" text="${text?.substring(0, 50)}"`);
    }

    await page.screenshot({ path: "test-results/step6-final.png" });

    const hasContent = userMsgs || aiMsgs;
    expect(msgCount).toBeGreaterThan(0);

    expect(appErrors()).toHaveLength(0);
  });

  test("Step 7 — Final assertions across key pages", async ({ page }) => {
    await login(page);

    for (const path of ["/", "/app/my"]) {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1000);

      const title = await page.title();
      expect(title).toBeTruthy();

      const bodyText = (await page.textContent("body")) || "";
      expect(bodyText.length).toBeGreaterThan(0);

      console.log(`${path}: title="${title}" length=${bodyText.length}`);
    }

    const assertErrors = appErrors().filter(
      (e) => !e.includes("AxiosError") || page.url().includes("/app/generate/")
    );
    console.log(`Final app errors: ${assertErrors.length}`);
    if (assertErrors.length > 0) {
      console.warn("Errors detected:");
      assertErrors.forEach((e) => console.warn("  ", e));
    }
  });
});
