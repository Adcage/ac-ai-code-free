# Task 9 Tests Integration And Acceptance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为第七阶段补齐关键测试、真实集成验证和最终验收记录，确保这次升级不是“能跑一次”，而是“有回归保护、有阶段出口”。

**Architecture:** 第七阶段前八个任务都在铺链路，但如果没有最后的验证闭环，整条链路仍然不可控。本任务统一收口测试和验收：先补关键单测，再跑一次后端回归、前端构建、真实 `vue_project` 生成、预览访问和部署访问，最后把结果写回总控文档。

**Tech Stack:** JUnit 5, Spring Boot Test, Maven Surefire, npm, 手工验收记录

---

## Files

- Modify: `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeTest.java`
- Create: `src/test/java/com/adcage/acaicodefree/ai/tools/FileWriteToolTest.java`
- Create: `src/test/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandlerTest.java`
- Create: `src/test/java/com/adcage/acaicodefree/core/build/VueProjectBuildServiceTest.java`
- Modify: `docs/plans/2026-04-14-phase-7-vue-project-generation.md`

## 验证范围

本任务要覆盖三层验证：

- 单元测试：验证工具、处理器、构建服务等关键点。
- 集成验证：验证真实 `vue_project` 生成主链路。
- 阶段验收：验证预览、部署、历史消息和旧模式回归。

## 详细步骤

### Step 1: 盘点测试缺口

先按模块列出缺口：

- 文件写入安全性
- JSON 流消息处理
- 构建服务命令执行
- Facade 新模式分流
- 旧模式是否仍可用

这个盘点结果要和前八个任务一一对应，避免最后测试覆盖不到关键变更点。

### Step 2: 补齐单元测试

优先补这几类测试：

- `FileWriteToolTest`
- `JsonMessageStreamHandlerTest`
- `VueProjectBuildServiceTest`
- `AiCodeGeneratorFacadeTest` 中新增 `vue_project` 分支相关验证

如果过程中发现某个类难以测试，优先重构为更小的可测方法，而不是放弃测试。

### Step 3: 跑后端测试

执行：

```bash
mvn test
```

预期：

- 新增测试全部通过。
- 老测试不因为 `vue_project` 改造而失败。

如果失败，记录失败属于哪一类：

- 配置问题
- 目录问题
- 流消息问题
- 构建服务问题

### Step 4: 跑前端校验

执行：

```bash
npm run type-check
npm run build
```

工作目录：`ac-ai-code-free-fronted/`

目标是确认前端新增的 `vue_project` 契约不会破坏现有构建。

### Step 5: 做真实模型集成验证

准备条件：

- 可用 API Key
- 可用 npm 环境
- 数据库可用

验证步骤：

1. 创建 `codeGenType=vue_project` 的应用。
2. 发起一次最小 Vue 工程生成请求。
3. 确认工具逐文件落盘。
4. 确认构建后出现 `dist`。
5. 确认预览地址可访问。
6. 确认部署地址可访问。

### Step 6: 做旧模式回归验证

至少各跑一次：

- `single_file`
- `multi-file`

确认结果：

- 仍能正常生成。
- SSE 前端显示未被破坏。
- 预览路径未被错误切换到 `dist`。

### Step 7: 更新总控文档

把 `docs/plans/2026-04-14-phase-7-vue-project-generation.md` 中的：

- 任务复选框
- 里程碑复选框
- 完成定义复选框
- 进度记录模板实例

全部按实际结果更新。

### Step 8: 提交

```bash
git add src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeTest.java src/test/java/com/adcage/acaicodefree/ai/tools/FileWriteToolTest.java src/test/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandlerTest.java src/test/java/com/adcage/acaicodefree/core/build/VueProjectBuildServiceTest.java docs/plans/2026-04-14-phase-7-vue-project-generation.md
git commit -m "test: add phase 7 verification coverage"
```

## 最终验收清单

- [ ] 可以创建 `codeGenType=vue_project` 的应用。
- [ ] AI 能按文件逐步生成 Vue 工程。
- [ ] 前端能实时看到 AI 回复和工具调用进度。
- [ ] 工具返回信息不泄露绝对路径。
- [ ] 同一应用多轮生成具备连续记忆。
- [ ] 生成完成后自动构建并产出 `dist`。
- [ ] 预览地址可以直接访问 `dist/index.html`。
- [ ] 部署复制的是 `dist` 目录。
- [ ] 聊天记录保存的是可读文本。
- [ ] 老模式没有被破坏。

## 风险说明

- 如果跳过真实模型集成验证，很多问题在单元测试阶段根本暴露不出来。
- 如果不做旧模式回归，`vue_project` 很可能在上线时带来隐藏回归。
