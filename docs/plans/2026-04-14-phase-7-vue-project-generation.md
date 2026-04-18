# Phase 7 Vue Project Generation Master Plan Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有 AI 代码生成功能从网页代码片段输出升级为可生成、可构建、可预览、可部署的 Vue 3 工程模式，并为每个实施任务提供独立的详细执行文档。

**Architecture:** 本计划采用“总控文档 + 分任务文档”的双层结构。总控文档只负责进度管理、任务依赖、阶段验收和跳转入口；每个任务文档单独描述要修改的文件、推荐测试顺序、最小实现路径、验证命令、风险点和完成标准，执行时按依赖顺序推进。

**Tech Stack:** Spring Boot 3.5.5, Java 21, LangChain4j, Reactor Flux, Hutool, MyBatis-Flex, Caffeine, Redis, Vue 3, Vue Router 4, Vite, Node.js 20+

---

## 使用说明

本文件不是代码实现文档，而是第七阶段的总控面板。

使用方式固定如下：

- 先看本文件确认当前整体进度。
- 选中一个未完成任务。
- 打开对应的任务文档执行。
- 执行完成后，先更新本文件中的任务复选框，再更新对应任务文档中的完成记录。
- 如果任务范围变更，先改总控文档中的依赖说明，再改子任务文档。

## 当前基线

基于当前仓库代码，实施前需要统一认知如下现状：

- 当前只支持 `single_file` 和 `multi-file`，还没有 `vue_project` 模式。
- `AppController#addApp` 仍然把 `codeGenType` 硬编码成 `multi-file`。
- `AiCodeGeneratorFacade` 仍然把流式结果视为纯文本，交给 `CodeFileSaverExecutor` 在流结束后统一解析保存。
- `AiCodeGenServiceFactory` 还是全局单例服务工厂，没有按 `appId + codeGenType` 隔离服务和记忆。
- SSE 当前只传纯文本，前端不会区分 AI 回复、工具请求、工具执行完成三类消息。
- 聊天记录落库仍然把原始流文本直接拼接保存，不适合保存结构化 JSON 消息。
- 预览和部署当前都基于源码目录，不是基于 Vue 工程构建后的 `dist` 目录。

## 执行顺序

执行顺序不建议打乱，推荐顺序如下：

1. Task 1 先补齐依赖和配置基线。
2. Task 2 打开 `vue_project` 模式入口和 Prompt 资源入口。
3. Task 3 实现专用模型 Bean、文件写入工具和目录约定。
4. Task 4 重构 AI Service 工厂和记忆加载。
5. Task 5 建立统一流消息模型和 Facade 新分支。
6. Task 6 接入流处理器并改造聊天记录落库逻辑。
7. Task 7 打通 Vue 工程构建、预览、部署。
8. Task 8 补齐 SSE 契约和前端解析说明。
9. Task 9 跑完整验证、补齐测试和验收清单。

## 任务面板

- [x] Task 1: 依赖升级与配置基线
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/01-task-1-dependency-and-config-baseline.md`

- [x] Task 2: 模式枚举、请求 DTO、控制层入口与 Prompt 资源
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/02-task-2-entrypoints-enum-dto-prompt.md`

- [x] Task 3: 推理模型 Bean、文件写入工具与工程目录规则
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/03-task-3-reasoning-model-and-file-write-tool.md`

- [x] Task 4: AI Service 工厂重构与聊天记忆加载
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/04-task-4-service-factory-and-chat-memory.md`

- [x] Task 5: 流消息协议与 Facade TokenStream 适配
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/05-task-5-stream-message-protocol-and-facade.md`

- [x] Task 6: 流处理器与聊天记录落库改造
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/06-task-6-stream-handlers-and-history-persistence.md`

- [x] Task 7: Vue 工程构建、预览与部署
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/07-task-7-build-preview-and-deploy.md`

- [x] Task 8: SSE 契约兼容与前端接入说明
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/08-task-8-sse-contract-and-frontend-integration.md`

- [x] Task 9: 单元测试、集成验证与阶段验收
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/09-task-9-tests-integration-and-acceptance.md`

## 里程碑勾选板

- [x] M1: 后端已经允许创建 `codeGenType=vue_project` 的应用。
- [x] M2: AI 可以通过工具逐文件把内容写入 `temp/code_output/vue_project_{appId}`。
- [x] M3: 同一应用多轮生成时，服务具备按 `appId` 绑定的连续记忆。
- [x] M4: `vue_project` 模式的流输出已经切换为统一 JSON 消息协议。
- [x] M5: 前端已经能显示 AI 回复和工具调用进度，而不是只显示纯文本。
- [x] M6: 生成结束后会自动执行 `npm install` 和 `npm run build`。
- [x] M7: 预览与部署均基于 `dist` 目录，而不是源码目录。
- [x] M8: 聊天记录保存为可读文本，不保存原始 JSON 流。
- [x] M9: 老的 `single_file` / `multi-file` 模式未被破坏。

## 任务依赖矩阵

| 任务 | 依赖任务 | 依赖原因 | 允许并行情况 |
| --- | --- | --- | --- |
| Task 1 | 无 | 为所有后续任务提供统一依赖和配置基线 | 不建议并行 |
| Task 2 | Task 1 | 入口枚举和 Prompt 依赖新的模式定义 | 可与 Task 3 后半段轻度并行 |
| Task 3 | Task 1, Task 2 | Bean、工具和目录命名需要模式值和配置前缀稳定 | 不建议并行 |
| Task 4 | Task 3 | 工厂重构需要使用新的模型 Bean 和文件工具 | 不建议并行 |
| Task 5 | Task 4 | Facade 新分支依赖 `generateVueProjectCodeStream()` | 可与 Task 6 设计联动，但代码实现仍建议顺序执行 |
| Task 6 | Task 5 | 处理器需要消费统一消息协议 | 不建议并行 |
| Task 7 | Task 3, Task 6 | 构建目录规则和落库逻辑都要先稳定 | 可在 Task 8 文档准备阶段并行 |
| Task 8 | Task 5, Task 6, Task 7 | 前端契约依赖最终流协议和预览地址 | 可和 Task 9 的文档准备并行 |
| Task 9 | Task 1-8 | 需要基于最终实现补齐回归验证 | 收尾任务 |

## 执行前检查清单

- [x] 已确认当前分支允许创建规划文档。
- [x] 已确认 `docs/plans/2026-04-14-phase-7-vue-project-generation/` 目录存在。
- [x] 已确认前端默认 Node 版本要求仍为 `^20.19.0 || >=22.12.0`。
- [x] 已确认本地具备可用的 `npm` 环境，后续构建服务测试时可执行命令。
- [x] 已确认后端测试环境可运行 `mvn test`。

## 完成定义

只有当下面所有项都勾选后，第七阶段才算完成：

- [x] 已完成 Task 1 到 Task 9 全部文档中的“完成标准”。
- [x] 已跑通至少一次真实的 `vue_project` 生成流程。
- [x] 已生成真实的 `dist` 产物目录。
- [x] 已通过预览地址访问页面成功。
- [x] 已通过部署地址访问页面成功。
- [x] 已确认聊天记录页面显示的是可读消息文本，而不是 JSON 原文。
- [x] 已确认旧模式仍能生成和预览。

## 进度记录模板

每次推进一个任务后，按下面格式记录：

```text
- 日期：2026-04-14
- 任务：Task 3
- 状态：进行中 / 已完成 / 阻塞
- 结果：
- 下一步：
- 风险：
```

- 日期：2026-04-14
- 任务：Task 1
- 状态：已完成
- 结果：对齐依赖基线后移除默认模型的 `response-format: json` / `strict-json-schema`，补齐 local 环境 `app.ai.vue-project.*` 关键配置映射，`AcAICodeFreeApplicationTests` 可稳定启动。
- 下一步：推进 Task 2 打开 `vue_project` 入口。
- 风险：LangChain4j 升级后旧测试调用风格不兼容，后续任务中需持续关注。

- 日期：2026-04-14
- 任务：Task 2
- 状态：已完成
- 结果：新增 `CodeGenTypeEnum.VUE_PROJECT`、`AppAddRequest.codeGenType`，`AppController#addApp` 改为显式校验并保存传入模式，不再硬编码 `multi-file`；新增 `codegen-vue-project-system-prompt.txt`。
- 下一步：推进 Task 3 落地模型 Bean 与文件写入工具。
- 风险：前端若未传 `codeGenType` 将直接参数错误，需要同步前端调用参数。

- 日期：2026-04-14
- 任务：Task 3
- 状态：已完成
- 结果：新增 `reasoningStreamingChatModel`、`FileWriteTool`、目录规则常量与 `FileWriteToolTest`，实现相对路径写入、路径穿越拦截、UTF-8 覆盖写与返回值脱敏；补充旧工厂的流式模型注入限定，避免双 Bean 冲突。
- 下一步：按依赖进入 Task 4（服务工厂重构与记忆加载）。
- 风险：`reasoningStreamingChatModel` 依赖 `app.ai.vue-project.api-key`，不同环境必须保证配置完整。

- 日期：2026-04-15
- 任务：Task 4-8
- 状态：已完成
- 结果：完成 `AiCodeGenServiceFactory` 按 `appId + codeGenType` 缓存重构并接入 `ChatMemoryLoader`；新增流消息模型与 Facade `vue_project` 分支；新增 `SimpleTextStreamHandler` / `JsonMessageStreamHandler` / `StreamHandlerExecutor` 并将聊天记录落库改为可读文本；新增 `VueProjectBuildService` 并在生成完成后触发 `npm install + npm run build`；前端完成 `codeGenType=vue_project` 创建入口、SSE 二层 JSON 兼容解析、`dist/index.html` 预览路径分流。
- 下一步：推进 Task 9 的真实模型集成验收（真实 key、真实落盘、真实预览和部署访问）并更新最终完成定义。
- 风险：真实模型联调依赖外部 API key 与运行环境，当前仅完成代码级与自动化测试级验证。

- 日期：2026-04-15
- 任务：Task 9
- 状态：进行中
- 结果：后端 `mvn test` 通过（63 tests, 0 failures, 0 errors, 6 skipped），前端 `npm run type-check` 与 `npm run build` 通过；修复前端历史类型问题（`tsconfig.json` 路径配置位置、多个页面的 `res.data.data` 空值收敛与分页字段可空处理）；新增 `AppChatE2ETest` 的 `vue_project` 端到端用例并扩展前端 `tests/chat-flow.e2e.test.mjs` 为 `single_file + vue_project` 双链路脚本。
- 下一步：补真实 `vue_project` 端到端验收记录与旧模式手工回归记录。
- 风险：未完成真实模型生成与部署地址人工访问前，不宜勾选阶段完成定义。

- 日期：2026-04-15
- 任务：Task 9
- 状态：已完成
- 结果：已完成真实链路严格收尾验收：`vue_project` 真实生成可触发工具写入并产出 `dist/index.html`；预览地址 `http://127.0.0.1:8711/api/static/vue_project_{appId}/dist/index.html` 可访问；部署地址返回并可访问 `.../api/static/{deployKey}/index.html`；聊天记录保持可读文本；旧模式 `single_file` 通过最小代码块生成并可访问预览。与此同时补齐后端健壮性修复：`@UserMessage` 标注、`chatMemoryProvider` 绑定、`npm ETARGET` 自动修复重试、部署 URL 规范化与 `index.html` 直达、单文件解析 fallback。
- 下一步：进入第八阶段规划或按需拆分提交。
- 风险：真实模型输出仍具不确定性，后续若更换模型需保留 `VueProjectBuildService` 的版本修复逻辑并持续监控安装失败日志。

## 任务分派建议

如果后续要让不同执行者并行处理，本文件可以作为分派入口：

- 负责基础设施的人优先领取 Task 1, Task 3, Task 4, Task 5, Task 6, Task 7。
- 负责前端契约的人优先领取 Task 2, Task 8。
- 负责验证闭环的人优先领取 Task 9。

但是正式编码时，仍然建议严格按照依赖顺序推进，不建议同时修改同一链路的关键文件。
