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

- [ ] Task 1: 依赖升级与配置基线
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/01-task-1-dependency-and-config-baseline.md`

- [ ] Task 2: 模式枚举、请求 DTO、控制层入口与 Prompt 资源
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/02-task-2-entrypoints-enum-dto-prompt.md`

- [ ] Task 3: 推理模型 Bean、文件写入工具与工程目录规则
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/03-task-3-reasoning-model-and-file-write-tool.md`

- [ ] Task 4: AI Service 工厂重构与聊天记忆加载
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/04-task-4-service-factory-and-chat-memory.md`

- [ ] Task 5: 流消息协议与 Facade TokenStream 适配
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/05-task-5-stream-message-protocol-and-facade.md`

- [ ] Task 6: 流处理器与聊天记录落库改造
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/06-task-6-stream-handlers-and-history-persistence.md`

- [ ] Task 7: Vue 工程构建、预览与部署
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/07-task-7-build-preview-and-deploy.md`

- [ ] Task 8: SSE 契约兼容与前端接入说明
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/08-task-8-sse-contract-and-frontend-integration.md`

- [ ] Task 9: 单元测试、集成验证与阶段验收
文档：`docs/plans/2026-04-14-phase-7-vue-project-generation/09-task-9-tests-integration-and-acceptance.md`

## 里程碑勾选板

- [ ] M1: 后端已经允许创建 `codeGenType=vue_project` 的应用。
- [ ] M2: AI 可以通过工具逐文件把内容写入 `temp/code_output/vue_project_{appId}`。
- [ ] M3: 同一应用多轮生成时，服务具备按 `appId` 绑定的连续记忆。
- [ ] M4: `vue_project` 模式的流输出已经切换为统一 JSON 消息协议。
- [ ] M5: 前端已经能显示 AI 回复和工具调用进度，而不是只显示纯文本。
- [ ] M6: 生成结束后会自动执行 `npm install` 和 `npm run build`。
- [ ] M7: 预览与部署均基于 `dist` 目录，而不是源码目录。
- [ ] M8: 聊天记录保存为可读文本，不保存原始 JSON 流。
- [ ] M9: 老的 `single_file` / `multi-file` 模式未被破坏。

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

- [ ] 已确认当前分支允许创建规划文档。
- [ ] 已确认 `docs/plans/2026-04-14-phase-7-vue-project-generation/` 目录存在。
- [ ] 已确认前端默认 Node 版本要求仍为 `^20.19.0 || >=22.12.0`。
- [ ] 已确认本地具备可用的 `npm` 环境，后续构建服务测试时可执行命令。
- [ ] 已确认后端测试环境可运行 `mvn test`。

## 完成定义

只有当下面所有项都勾选后，第七阶段才算完成：

- [ ] 已完成 Task 1 到 Task 9 全部文档中的“完成标准”。
- [ ] 已跑通至少一次真实的 `vue_project` 生成流程。
- [ ] 已生成真实的 `dist` 产物目录。
- [ ] 已通过预览地址访问页面成功。
- [ ] 已通过部署地址访问页面成功。
- [ ] 已确认聊天记录页面显示的是可读消息文本，而不是 JSON 原文。
- [ ] 已确认旧模式仍能生成和预览。

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

## 任务分派建议

如果后续要让不同执行者并行处理，本文件可以作为分派入口：

- 负责基础设施的人优先领取 Task 1, Task 3, Task 4, Task 5, Task 6, Task 7。
- 负责前端契约的人优先领取 Task 2, Task 8。
- 负责验证闭环的人优先领取 Task 9。

但是正式编码时，仍然建议严格按照依赖顺序推进，不建议同时修改同一链路的关键文件。
