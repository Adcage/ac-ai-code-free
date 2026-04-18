# Task 1 Dependency And Config Baseline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `vue_project` 模式建立稳定的依赖和配置基线，确保后续工具调用、记忆隔离、流式协议和构建流程都有统一的底座可用。

**Architecture:** 这一任务只处理依赖升级和配置补齐，不提前混入业务实现。先把 `pom.xml` 和 `application.yml` 调整到支持第七阶段的状态，再通过最小的 Spring 上下文验证确保不会出现 Bean 冲突或配置绑定失败。

**Tech Stack:** Maven, Spring Boot 3.5.5, LangChain4j, Caffeine, Redis, application.yml

---

## 目标范围

本任务只做下面这些事情：

- 统一 LangChain4j 版本线。
- 补齐 `caffeine` 依赖。
- 补齐 Redis 记忆依赖或至少为后续记忆实现预留依赖。
- 在 `application.yml` 中新增 `app.ai.vue-project.*` 配置组。
- 确保默认流式模型和 `vue_project` 专用模型的配置职责边界清晰。

本任务明确不做：

- 不创建 `vue_project` 枚举。
- 不实现 `FileWriteTool`。
- 不实现 `AiCodeGenServiceFactory` 重构。
- 不修改流消息协议。

## Files

- Modify: `pom.xml`
- Modify: `src/main/resources/application.yml`
- Test: `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeTest.java`

## 当前问题

当前代码存在的配置问题如下：

- `pom.xml` 中 LangChain4j 还是 `1.0.0-beta3`，后续工具流和流式回调能力风险较高。
- 还没有 `caffeine` 和 Redis 依赖，后续无法自然承接服务缓存和可替换记忆实现。
- `application.yml` 只有默认 `chat-model` 和 `streaming-chat-model` 配置。
- 默认模型当前开启了 `response-format: json` 和 `strict-json-schema: true`，这不适合未来的工具调用型 `vue_project` 模式。

## 详细步骤

### Step 1: 先写一个最小上下文加载验证说明

先在任务执行记录里明确这次改动的验证目标：

- Spring 容器能正常启动。
- 默认聊天模型仍可注入。
- 新增的 `app.ai.vue-project.*` 配置不会造成绑定异常。

如果需要新增专门测试，可在后续任务中补 `config` 级测试；本任务先复用现有 `AiCodeGeneratorFacadeTest` 做 smoke test。

### Step 2: 修改 `pom.xml`

把依赖调整为同一版本线，优先原则如下：

- `dev.langchain4j:langchain4j`
- `dev.langchain4j:langchain4j-open-ai-spring-boot-starter`
- `dev.langchain4j:langchain4j-reactor`

三者必须使用同一版本，不能混搭。

新增依赖：

```xml
<dependency>
    <groupId>com.github.ben-manes.caffeine</groupId>
    <artifactId>caffeine</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

注意点：

- 不要在本任务里顺手引入多余 AI 框架。
- 不要同时改动和本阶段无关的 Maven 插件。
- 保持改动最小，只做第七阶段必须项。

### Step 3: 修改 `application.yml`

新增配置块时，目标结构参考下面格式：

```yml
app:
  ai:
    vue-project:
      base-url: https://api.deepseek.com
      api-key: ${DEEPSEEK_API_KEY}
      dev-model-name: deepseek-chat
      prod-model-name: deepseek-reasoner
      dev-max-tokens: 8192
      prod-max-tokens: 32768
      memory-window-size: 20
      install-timeout-seconds: 300
      build-timeout-seconds: 180
```

实施时注意三点：

- 不要给 `vue_project` 专用模型强绑 `response-format: json`。
- 默认老模式可以先保留现有 starter 配置，减少回归风险。
- API Key 推荐改成环境变量读取，不要继续保留硬编码示例值作为正式方案。

### Step 4: 检查配置职责边界

修改完成后，人工复核一次配置分层：

- 默认 `langchain4j.open-ai.*` 继续服务旧模式。
- `app.ai.vue-project.*` 只为即将新增的专用 Bean 服务。
- 不要在本任务里就试图通过 `application.yml` 同时把所有模式都切到新模型。

### Step 5: 运行最小验证

执行：

```bash
mvn -Dtest=AiCodeGeneratorFacadeTest test
```

预期：

- 测试至少能启动 Spring 上下文。
- 不出现配置绑定异常。
- 不出现依赖冲突或 Bean 重复注入异常。

如果失败，优先排查：

- LangChain4j 三个依赖版本是否一致。
- `application.yml` 缩进是否正确。
- Redis 依赖引入后是否触发新的自动配置要求。

### Step 6: 记录变更影响

在任务记录里写清楚三类变化：

- 相比之前，多了哪些依赖能力。
- 相比之前，配置层从“单模型”变成“老模式默认模型 + Vue 工程专用配置组”。
- 相比之前，后续任务可以直接消费哪些配置项。


如果本任务没有修改测试文件，则从 `git add` 中去掉该测试文件。

## 验收标准

- `pom.xml` 已经补齐第七阶段需要的依赖。
- `application.yml` 已经存在 `app.ai.vue-project.*` 配置组。
- 老模式的 Spring 容器仍然可以正常启动。
- 配置中没有把工具调用场景错误地强制成严格 JSON 输出。

## 风险与回退

- 最大风险是 LangChain4j 升级后现有 API 接口有小幅变动。
- 次要风险是 Redis 自动配置引入后影响本地启动。
- 如果依赖升级引入连锁问题，优先回退到同一主版本线中更保守的小版本，而不是继续混搭版本。

## 完成记录

- 日期：2026-04-14
- 状态：已完成
- 结果：`pom.xml` 已具备 LangChain4j 同版本线、`caffeine` 与 Redis 依赖；`application.yml` / `application-local.yml` 移除了与新版本不兼容的 `response-format: json` 与 `strict-json-schema`，并保留 `app.ai.vue-project.*` 配置组。
- 验证：`mvn clean "-Dtest=AcAICodeFreeApplicationTests" test` 通过。
