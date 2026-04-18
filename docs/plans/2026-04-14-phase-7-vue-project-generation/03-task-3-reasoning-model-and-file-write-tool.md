# Task 3 Reasoning Model And File Write Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新增 `vue_project` 模式专用推理模型 Bean 和文件写入工具，让模型具备按应用目录逐文件落盘的正式能力。

**Architecture:** 这个任务是第七阶段的真正底座。通过单独的模型 Bean 与 `FileWriteTool`，把“AI 生成文本”转成“AI 调工具写文件”；同时把工程目录命名规则固定下来，防止工具层到处拼接路径、泄露绝对路径或串应用写入。

**Tech Stack:** Spring Configuration, LangChain4j Tool, Java NIO, AppConstant

---

## Files

- Create: `src/main/java/com/adcage/acaicodefree/config/ReasoningStreamingChatModelConfig.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`
- Modify: `src/main/java/com/adcage/acaicodefree/constant/AppConstant.java`
- Test: `src/test/java/com/adcage/acaicodefree/ai/tools/FileWriteToolTest.java`

## 当前问题

当前项目还没有下面这些能力：

- 没有 `reasoningStreamingChatModel` 之类的专用流式模型 Bean。
- 没有 LangChain4j 工具方法可让模型按文件写入。
- `AppConstant` 只定义了统一输出目录，没有 `vue_project_{appId}` 这种明确约定。
- 还没有路径穿越防护、相对路径校验和 UTF-8 覆盖写入规范。

## 详细步骤

### Step 1: 先写 `FileWriteToolTest`

测试优先覆盖四个核心场景：

```java
@Test
void writeFileShouldCreateParentDirectoriesAndWriteUtf8Content() {}

@Test
void writeFileShouldRejectAbsolutePath() {}

@Test
void writeFileShouldRejectPathTraversal() {}

@Test
void writeFileShouldReturnRelativePathOnly() {}
```

测试目标不是验证 LangChain4j，而是验证你自己的文件系统约束逻辑。

### Step 2: 修改 `AppConstant`

补充目录规则辅助常量或辅助方法，至少要让下面这些含义可复用：

- Vue 工程源码目录前缀 `vue_project_`
- 构建产物目录 `dist`
- 生成目录根路径 `temp/code_output`
- 部署目录根路径 `temp/code_deploy`

不要把所有逻辑都塞成字符串拼接散落在各个类里，最少要把命名规则集中到常量层或一个极小的目录构造方法中。

### Step 3: 新建 `ReasoningStreamingChatModelConfig`

配置类职责要单一：

- 读取 `app.ai.vue-project.*` 配置。
- 构建命名清晰的 `StreamingChatLanguageModel` Bean。
- Bean 名称要显式区分于默认 starter 自动注入 Bean。

建议输出 Bean 名称：

```java
@Bean("reasoningStreamingChatModel")
public StreamingChatLanguageModel reasoningStreamingChatModel() {
    // 按环境或配置选择 dev/prod 模型名
}
```

不要在这个类里同时构建 AI Service，不要越权承担工厂职责。

### Step 4: 新建 `FileWriteTool`

工具签名目标：

```java
@Tool("写入文件到指定路径")
public String writeFile(String relativeFilePath, String content, Long appId)
```

如果当前 LangChain4j 版本支持 `@ToolMemoryId`，优先按正式注解使用；如果版本约束暂时不支持，再评估兼容替代方案，但计划目标仍然是绑定 `appId`。

实现规则必须写死：

- 只接受相对路径。
- 拒绝绝对路径。
- 拒绝 `..` 越界路径。
- 自动创建父目录。
- 使用覆盖写，不做追加写入。
- 统一 UTF-8。
- 返回值只能是 `文件写入成功：src/App.vue` 这类相对路径文本。

### Step 5: 处理目录归一化

实现时一定要做标准化处理，例如：

```java
Path normalized = projectRoot.resolve(relativeFilePath).normalize();
if (!normalized.startsWith(projectRoot)) {
    throw new BusinessException(ErrorCode.PARAMS_ERROR, "非法文件路径");
}
```

这一段是整个工具安全性的核心，不能省略。

### Step 6: 运行工具测试

执行：

```bash
mvn -Dtest=FileWriteToolTest test
```

预期：

- 正常路径可写入。
- 越界路径和绝对路径被拒绝。
- 工具返回值不包含盘符、绝对目录或服务器真实路径。

### Step 7: 手工检查生成目录结构

即使单测通过，也要做一次手工检查：

1. 用测试或临时调用方式写入 `package.json`。
2. 确认目录真实落在 `temp/code_output/vue_project_{appId}`。
3. 确认没有写到仓库根目录或其他应用目录。

### Step 8: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/config/ReasoningStreamingChatModelConfig.java src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java src/main/java/com/adcage/acaicodefree/constant/AppConstant.java src/test/java/com/adcage/acaicodefree/ai/tools/FileWriteToolTest.java
git commit -m "feat: add vue project file writing tool"
```

## 验收标准

- 已存在独立的 `reasoningStreamingChatModel` Bean。
- `FileWriteTool` 能按 `appId` 写入 `vue_project_{appId}` 目录。
- 工具可以自动创建父目录并覆盖写入。
- 工具拒绝绝对路径和路径穿越。
- 返回信息不泄露绝对路径。

## 风险说明

- 如果路径归一化没做好，后面所有安全假设都会失效。
- 如果工具返回绝对路径，前端和模型都可能看到服务器真实目录结构。

## 完成记录

- 日期：2026-04-14
- 状态：已完成
- 结果：已新增 `ReasoningStreamingChatModelConfig`、`FileWriteTool`、`FileWriteToolTest`，并在 `AppConstant` 中固化 `vue_project_` 目录规则、`dist` 目录名和路径辅助方法；`AiCodeGenServiceFactory` 已显式绑定旧流式模型，避免双 Bean 注入冲突。
- 验证：`mvn clean "-Dtest=FileWriteToolTest" test` 通过，且 `mvn clean "-Dtest=AcAICodeFreeApplicationTests,AppControllerTest,FileWriteToolTest" test` 通过。
