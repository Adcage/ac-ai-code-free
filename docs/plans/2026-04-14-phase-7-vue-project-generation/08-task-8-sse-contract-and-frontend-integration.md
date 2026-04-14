# Task 8 Sse Contract And Frontend Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不破坏旧 SSE 外层结构的前提下，让前端能够识别 `vue_project` 模式的二层 JSON 消息，并正确刷新新的 `dist` 预览地址。

**Architecture:** 本任务不推倒现有 SSE 接口，而是走兼容升级路线。后端保持外层 `{"d":"..."}` envelope 不变，`vue_project` 模式只是在 `d` 内部放入统一的 JSON 消息；前端在识别到新模式时做二次解析，并把工具进度转成用户可读显示。

**Tech Stack:** Spring SSE, Vue 3, EventSource, TypeScript, Frontend Docs

---

## Files

- Modify: `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- Modify: `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
- Modify: `ac-ai-code-free-fronted/src/pages/HomePage.vue`
- Modify: `ac-ai-code-free-fronted/src/api/typings.d.ts`
- Modify: `docs/learn/AI-CodeGen-Frontend-Implementation.md`

## 当前问题

当前前端有三类不匹配：

- 创建应用时只传 `initPrompt`，没有传 `codeGenType`。
- SSE 消息只按纯文本 `data.d` 处理。
- 预览地址固定为 `${codeGenType}_${appId}/index.html`，不适配 `vue_project/dist/index.html`。

## 详细步骤

### Step 1: 先梳理前端契约变化

在任务开始前，先明确需要变更的契约：

- `addApp` 请求体增加 `codeGenType`。
- `chat/gen/code/stream` 外层 SSE 不变。
- `vue_project` 模式下 `d` 字段内部为二层 JSON。
- 预览路径切换为 `/api/static/vue_project_{appId}/dist/index.html`。

这一段梳理要先写进文档，避免后端和前端分别按不同理解修改。

### Step 2: 修改后端 SSE 说明点

通常 `AppController#chatToGenCode()` 的外层封装可以保持不变：

```java
Map<String, String> data = Map.of("d", chunk);
```

这里需要确认的是：

- 老模式 `chunk` 仍是纯文本。
- 新模式 `chunk` 是 `StreamMessage` 的 JSON 字符串。

后端这一步重点是“保持兼容”，而不是推翻接口。

### Step 3: 修改前端创建应用入口

在 `HomePage.vue` 中把：

```ts
addApp({ initPrompt: searchText.value })
```

改成显式传入：

```ts
addApp({
  initPrompt: searchText.value,
  codeGenType: 'vue_project',
})
```

同时更新 `typings.d.ts` 里的 `AppAddRequest` 类型定义。

### Step 4: 修改 `AppGeneratorPage.vue` 的 SSE 解析

解析顺序建议固定为：

1. 先 `JSON.parse(rawData)` 得到外层对象。
2. 取出 `data.d`。
3. 如果当前应用是老模式，直接按文本拼接。
4. 如果当前应用是 `vue_project`，再对 `data.d` 做二次 `JSON.parse`。
5. 根据消息类型追加不同展示内容。

建议显示文本：

- `ai_response` -> 直接追加自然语言文本。
- `tool_request` -> 追加 `[工具调用] 准备写入文件 ...`。
- `tool_executed` -> 追加 `[工具完成] 已写入文件 ...`。

### Step 5: 修改预览地址

在 `updatePreview()` 中按模式分支：

- 老模式继续使用 `${codeGenType}_${appId}/index.html`
- `vue_project` 使用 `vue_project_${appId}/dist/index.html`

不要直接拿 `app.value?.codeGenType` 拼原始路径，否则 `vue_project` 会少掉 `dist` 段。

### Step 6: 更新学习文档

`docs/learn/AI-CodeGen-Frontend-Implementation.md` 需要补充这些内容：

- 新老模式 SSE 二层解析差异。
- `vue_project` 模式下的预览地址规则。
- 为什么 `d` 字段内部不再一定是纯文本。

这部分文档的作用不是给用户看，而是给后续维护者快速建立正确认知。

### Step 7: 运行前端验证

执行：

```bash
npm run type-check
npm run build
```

工作目录：`ac-ai-code-free-fronted/`

手工验证：

1. 创建一个 `vue_project` 应用。
2. 打开生成页面。
3. 观察聊天区能否显示工具进度。
4. 观察预览 iframe 能否成功打开 `dist/index.html`。

### Step 8: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/controller/AppController.java ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue ac-ai-code-free-fronted/src/pages/HomePage.vue ac-ai-code-free-fronted/src/api/typings.d.ts docs/learn/AI-CodeGen-Frontend-Implementation.md
git commit -m "feat: support vue project stream messages in frontend"
```

## 验收标准

- 前端创建应用时会显式传 `codeGenType=vue_project`。
- 前端可以兼容解析老模式和新模式 SSE。
- `vue_project` 预览地址使用 `dist/index.html`。
- 前端文档已补充新的 SSE 解析规则。

## 风险说明

- 如果前端直接无条件二次 JSON 解析，会破坏老模式。
- 如果预览地址不分模式处理，Vite 工程资源会加载失败。
