import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const PYTHON = "http://localhost:9000";

test.describe("Prompt Capture E2E Verification", () => {
  const errors: string[] = [];

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
      if (url.includes("hmr") || url.includes("hot-update") || url.includes("vite")) return;
      errors.push(`[NETWORK] ${request.failure()?.errorText} — ${url}`);
    });

    page.on("response", (response) => {
      if (response.status() >= 500) {
        errors.push(`[SERVER 5xx] ${response.status()} — ${response.url()}`);
      }
    });
  });

  test.afterEach(async ({}, testInfo) => {
    const realErrors = errors.filter(
      (e) =>
        !e.includes("favicon") &&
        !e.includes("iconfont") &&
        !e.includes("hot-update") &&
        !e.includes("vite") &&
        !e.includes("hmr") &&
        !e.includes("user/get/login") &&
        !e.includes("AxiosError")
    );
    if (realErrors.length > 0 && testInfo.status !== "failed") {
      console.warn(`[${testInfo.title}] Unexpected errors (${realErrors.length}):`);
      realErrors.forEach((e) => console.warn("  ", e));
    }
  });

  function getPromptCaptureDir(): string {
    for (const base of ["../../../debug/prompts", "debug/prompts", "E:/Programme/Project/ac-ai-code-free/debug/prompts"]) {
      const abs = path.resolve(base);
      if (fs.existsSync(abs)) return abs;
    }
    return path.resolve("../../../debug/prompts");
  }

  function getPromptCaptureRuns(): string[] {
    const captureDir = getPromptCaptureDir();
    if (!fs.existsSync(captureDir)) return [];
    return fs.readdirSync(captureDir).filter((name) => {
      const p = path.join(captureDir, name);
      return fs.statSync(p).isDirectory();
    });
  }

  function getRunFiles(runId: string): { name: string; size: number }[] {
    const runDir = path.join(getPromptCaptureDir(), runId);
    if (!fs.existsSync(runDir)) return [];
    return fs.readdirSync(runDir).map((name) => {
      const p = path.join(runDir, name);
      return { name, size: fs.statSync(p).size };
    });
  }

  test("Step 1 — Verify Python backend is running and prompt capture is enabled", async ({ request }) => {
    const healthResp = await request.get(`${PYTHON}/health`);
    expect(healthResp.ok()).toBeTruthy();

    const statusResp = await request.get(`${PYTHON}/debug/prompt-capture/status`);
    expect(statusResp.ok()).toBeTruthy();
    const status = await statusResp.json();
    console.log(`Prompt capture: enabled=${status.prompt_capture_enabled}, dir=${status.prompt_capture_dir}`);

    if (!status.prompt_capture_enabled) {
      console.warn("PROMPT_CAPTURE_ENABLED is false — set it to true on the Python backend (.env or env var)");
    }
    expect(status.prompt_capture_enabled).toBe(true);
  });

  test("Step 2 — Register, login, create app, trigger generation, verify prompt capture files", async ({ page }) => {
    test.setTimeout(180000);
    const runsBefore = getPromptCaptureRuns();
    console.log(`Prompt capture runs before: ${runsBefore.length}`);

    const UNIQUE = Date.now().toString(36);
    const account = `pcap${UNIQUE}`;
    const password = "Test123456!";

    await page.goto("/user/register");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    await page.getByRole("textbox", { name: "* 账号" }).fill(account);
    const pwFields = page.locator('input[type="password"]');
    for (let i = 0; i < Math.min(await pwFields.count(), 2); i++) {
      await pwFields.nth(i).fill(password);
    }
    await page.getByRole("button", { name: "注册" }).click();
    await page.waitForTimeout(2000);
    await page.waitForLoadState("networkidle");
    expect(page.url()).toMatch(/\/user\/login/);

    await page.getByRole("textbox", { name: "* 账号" }).fill(account);
    await page.getByRole("textbox", { name: "* 密码" }).fill(password);
    await page.getByRole("button", { name: "登录" }).click();
    await page.waitForTimeout(2000);
    await page.waitForLoadState("networkidle");
    expect(page.url()).not.toMatch(/\/user\/login/);
    console.log(`Logged in: ${account}`);

    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    const ta = page.locator('textarea[placeholder*="描述你想要的"]').first();
    expect(await ta.count()).toBeGreaterThan(0);

    const prompt = "创建一个简单的HTML登录表单页面";
    await ta.fill(prompt);
    await page.locator(".send-btn").first().click();
    console.log("Sent generation request");

    await page.waitForTimeout(5000);

    const currentUrl = page.url();
    console.log(`URL after send: ${currentUrl}`);
    expect(currentUrl).toMatch(/\/app\/generate\//);

    try {
      const toolCards = page.locator(".tool-call-card");
      await toolCards.first().waitFor({ state: "visible", timeout: 90000 });
      console.log("Tool call cards appeared — generation active");
    } catch {
      console.log("No tool call cards, waiting for text response...");
    }

    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(5000);
      const current = getPromptCaptureRuns();
      const freshRuns = current.filter((r) => !runsBefore.includes(r));
      if (freshRuns.length > 0) {
        console.log(`Found new runs after ${(i + 1) * 5}s: ${freshRuns.join(", ")}`);
        break;
      }
      console.log(`Waiting for prompt capture... (${(i + 1) * 5}s)`);
    }

    const aiMsgs = page.locator(".message-item.ai-msg");
    console.log(`AI messages: ${await aiMsgs.count()}`);

    const runsAfter = getPromptCaptureRuns();
    console.log(`Prompt capture runs after: ${runsAfter.length}`);
    const newRuns = runsAfter.filter((r) => !runsBefore.includes(r));
    console.log(`New runs: ${newRuns.join(", ") || "none"}`);

    expect(newRuns.length).toBeGreaterThan(0);

    for (const runId of newRuns) {
      const files = getRunFiles(runId);
      console.log(`Run ${runId}: ${files.length} files`);
      for (const f of files) console.log(`  ${f.name} (${f.size} bytes)`);

      const runDir = path.join(getPromptCaptureDir(), runId);

      const indexFile = files.find((f) => f.name === "index.json");
      expect(indexFile).toBeDefined();

      if (indexFile) {
        const indexContent = fs.readFileSync(path.join(runDir, "index.json"), "utf-8");
        const index = JSON.parse(indexContent);

        expect(index.agent_run_id).toBeDefined();
        expect(typeof index.agent_run_id).toBe("number");
        expect(index.timestamp).toBeDefined();
        expect(index.code_gen_type).toBeDefined();
        expect(index.run_mode).toBeDefined();
        expect(index.user_prompt).toBeDefined();
        expect(typeof index.user_prompt).toBe("string");
        expect(index.total_iterations).toBeGreaterThan(0);
        expect(Array.isArray(index.chain)).toBe(true);
        expect(index.chain.length).toBeGreaterThan(0);

        for (const entry of index.chain) {
          expect(entry.seq).toBeGreaterThan(0);
          expect(["plan", "implement"]).toContain(entry.mode);
          expect(entry.iteration).toBeGreaterThan(0);
          expect(entry.file).toBeDefined();
          expect(entry.file).toMatch(/\.md$/);
        }

        if (index.enhance_prompt) {
          expect(index.enhance_prompt.file).toBeDefined();
          expect(index.enhance_prompt.model).toBeDefined();
        }

        console.log(`  index.json: agent_run_id=${index.agent_run_id}, iterations=${index.total_iterations}, chain=${index.chain.length}`);
      }

      const mdFiles = files.filter((f) => f.name.endsWith(".md"));
      expect(mdFiles.length).toBeGreaterThan(0);

      for (const mdFile of mdFiles) {
        const mdContent = fs.readFileSync(path.join(runDir, mdFile.name), "utf-8");
        expect(mdContent.length).toBeGreaterThan(100);

        if (mdFile.name === "enhance_prompt.md") {
          expect(mdContent).toContain("Enhance Prompt");
          expect(mdContent).toContain("Original Prompt");
          expect(mdContent).toContain("Enhanced Prompt");
          expect(mdContent).toContain("LLM Messages");
        } else {
          expect(mdContent).toContain("System Prompt");
          expect(mdContent).toContain("User Message");
          expect(mdContent).toContain("Model Response");
          expect(mdContent).toMatch(/<details>/);
          expect(mdContent).toMatch(/<\/details>/);
        }
        console.log(`  ${mdFile.name}: valid (${mdContent.length} chars)`);
      }
    }
  });

  test("Step 3 — Final error check", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    expect(await page.title()).toBeTruthy();
    expect(((await page.textContent("body")) || "").length).toBeGreaterThan(50);

    const realErrors = errors.filter(
      (e) =>
        !e.includes("favicon") &&
        !e.includes("iconfont") &&
        !e.includes("hot-update") &&
        !e.includes("vite") &&
        !e.includes("hmr") &&
        !e.includes("user/get/login") &&
        !e.includes("AxiosError")
    );
    if (realErrors.length > 0) {
      console.warn(`Final errors (${realErrors.length}):`);
      realErrors.forEach((e) => console.warn("  ", e));
    }
    expect(realErrors).toHaveLength(0);
  });
});
