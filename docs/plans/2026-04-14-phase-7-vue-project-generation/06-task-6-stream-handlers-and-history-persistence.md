# Task 6 Stream Handlers And History Persistence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把老模式纯文本流和 `vue_project` 模式 JSON 流分别交给独立处理器处理，并把聊天记录存储从“原始拼接”升级为“用户可读文本”。

**Architecture:** 当前 `AppServiceImpl` 同时承担了业务编排、流拼接和历史落库职责，已经过载。本任务通过 `SimpleTextStreamHandler`、`JsonMessageStreamHandler`、`StreamHandlerExecutor` 三个类把模式分流职责抽出，让服务层只负责保存用户消息、调用生成入口和委托处理器完成 AI 消息整理。

**Tech Stack:** Reactor Flux, Spring Service, JSON Parsing, Chat Persistence

---

## Files

- Create: `src/main/java/com/adcage/acaicodefree/core/handler/SimpleTextStreamHandler.java`
- Create: `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`
- Create: `src/main/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutor.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- Test: `src/test/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandlerTest.java`
- Test: `src/test/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutorTest.java`

## 当前问题

当前 `AppServiceImpl#chatToGenCode()` 的问题非常集中：

- 直接用 `StringBuilder` 拼接所有 chunk。
- 不关心消息类型。
- 流结束后直接把原始内容存成一条 AI 历史消息。
- 这套逻辑对旧模式能工作，但对 `vue_project` 会让聊天记录里塞满 JSON 原文或无意义碎片。

## 详细步骤

### Step 1: 先写处理器测试

最小测试覆盖下面几类断言：

```java
@Test
void simpleTextHandlerShouldAppendRawTextForLegacyModes() {}

@Test
void jsonMessageHandlerShouldAppendAiResponseText() {}

@Test
void jsonMessageHandlerShouldShowToolRequestOnlyOncePerId() {}

@Test
void jsonMessageHandlerShouldUseToolExecutedAsFinalTrustedFileEvent() {}
```

### Step 2: 新建 `SimpleTextStreamHandler`

职责非常单纯：

- 原样透传纯文本给前端。
- 收集最终完整 AI 文本。
- 在成功或失败时生成适合保存的消息内容。

这个类不要做 JSON 判断，不要做模式判断，只服务旧模式。

### Step 3: 新建 `JsonMessageStreamHandler`

核心规则需要写死：

- `ai_response`：把 `data` 追加到前端展示文本和历史文本。
- `tool_request`：同一个 `id` 只在首次提示时向前端显示一次。
- `tool_executed`：把最终写入成功信息整理为可读文本，例如 `已写入文件 src/router/index.js`。

不要把完整文件内容反复透传给前端，这会迅速把会话流打爆。第七阶段优先显示相对路径和少量摘要。

### Step 4: 新建 `StreamHandlerExecutor`

这个执行器只负责一件事：按 `CodeGenTypeEnum` 路由处理器。

目标映射：

- `SINGLE_FILE` -> `SimpleTextStreamHandler`
- `MULTI_FILE` -> `SimpleTextStreamHandler`
- `VUE_PROJECT` -> `JsonMessageStreamHandler`

不要在执行器里重新实现具体处理逻辑。

### Step 5: 修改 `AppServiceImpl`

这里的改造重点不是“改更多代码”，而是把现有责任拆开：

- 保存用户消息逻辑保留。
- 调用 `AiCodeGeneratorFacade` 逻辑保留。
- 原先在服务层里直接拼接 AI 文本的逻辑移交给处理器。
- `doOnComplete()` 和 `doOnError()` 中保存的内容，改成处理器整理后的最终可读文本。

实现后应达到的效果是：

- 老模式行为不变。
- 新模式聊天记录不会直接保存 JSON 原文。

### Step 6: 运行处理器测试

执行：

```bash
mvn -Dtest=JsonMessageStreamHandlerTest,StreamHandlerExecutorTest test
```

如果两个测试类名字最终不同，按实际名字执行。

### Step 7: 做一次数据库落库检查

人工验证：

1. 触发一次 `vue_project` 生成。
2. 查看对应 `chat_history.message`。
3. 确认内容是可读文本，例如“已写入文件 src/main.js”，而不是 `{"type":"tool_request"...}` 这种原始 JSON。

### Step 8: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/core/handler/SimpleTextStreamHandler.java src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java src/main/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutor.java src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java src/test/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandlerTest.java src/test/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutorTest.java
git commit -m "refactor: separate stream handling by generation mode"
```

## 验收标准

- 老模式继续按纯文本处理。
- `vue_project` 模式按统一 JSON 消息处理。
- 同一工具请求不会重复刷屏。
- 数据库存储内容为用户可读文本，不是原始 JSON 流。

## 风险说明

- 如果工具请求事件和执行完成事件处理混乱，前端会出现重复提示或错误提示。
- 如果服务层和处理器职责没切清，后续排查落库问题会非常困难。
