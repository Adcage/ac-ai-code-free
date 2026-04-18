# Task 4 Service Factory And Chat Memory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将全局单例 AI Service 工厂升级为按 `appId + codeGenType` 隔离的服务构建器，并引入可回放聊天记录的记忆加载能力。

**Architecture:** `vue_project` 模式需要专用模型、专用工具和专用记忆，因此不能继续复用当前那个“所有模式通吃”的单例工厂。本任务把服务创建职责重新拆清：工厂负责选择模型、工具和记忆并做缓存，记忆加载器负责从历史对话中恢复上下文，不让业务服务类继续堆积组装逻辑。

**Tech Stack:** LangChain4j AiServices, Caffeine, Chat Memory, Spring Component

---

## Files

- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
- Create: `src/main/java/com/adcage/acaicodefree/core/memory/ChatMemoryLoader.java`
- Test: `src/test/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactoryTest.java`

## 当前问题

当前工厂类问题很集中：

- 只有一个 `@Bean` 暴露统一 `AiCodeGeneratorService`。
- 工厂没有缓存键概念。
- 没有按 `appId` 恢复历史上下文。
- 老模式和新模式未来会共享同一套 Service，这会让工具和记忆污染旧链路。

## 详细步骤

### Step 1: 先写工厂测试草案

测试至少覆盖下面三个意图：

```java
@Test
void shouldCacheServiceByAppIdAndCodeGenType() {}

@Test
void shouldBuildVueProjectServiceWithToolAndMemory() {}

@Test
void shouldBuildLegacyServiceWithoutVueProjectTooling() {}
```

如果短期不方便把 LangChain4j 实例做成完全可断言对象，至少把“缓存键生成”和“分支选择逻辑”抽成可单测的方法。

### Step 2: 修改 `AiCodeGeneratorService`

新增方法签名：

```java
@SystemMessage(fromResource = "prompt/codegen-vue-project-system-prompt.txt")
Flux<String> generateVueProjectCodeStream(Long appId, String userMessage);
```

如果 LangChain4j 版本支持 `@MemoryId`，这里优先使用：

```java
Flux<String> generateVueProjectCodeStream(@MemoryId Long appId, String userMessage);
```

关键点：

- 新方法只为 `vue_project` 服务。
- 不要修改旧模式方法签名，减少回归面。

### Step 3: 新建 `ChatMemoryLoader`

这个组件只负责做一件事：

- 查最近 N 条聊天记录。
- 把 `user` / `ai` 消息转换成 LangChain4j 可识别的记忆消息对象。
- 装载到窗口型 ChatMemory。

不要把下面逻辑继续塞进 `AppServiceImpl`：

- 查表
- 转消息类型
- 构建记忆窗口
- 设置记忆上限

这正是需要抽组件的原因。

### Step 4: 重构 `AiCodeGenServiceFactory`

核心改造目标：

- 删除“统一单例 Service”假设。
- 增加缓存键，例如 `appId + ":" + codeGenType`。
- `vue_project` 模式下挂载：
  - `reasoningStreamingChatModel`
  - `FileWriteTool`
  - ChatMemory
- 老模式继续返回普通 Service。

伪代码结构建议：

```java
public AiCodeGeneratorService getService(Long appId, CodeGenTypeEnum codeGenType) {
    String key = buildCacheKey(appId, codeGenType);
    return cache.get(key, ignored -> createService(appId, codeGenType));
}
```

### Step 5: 控制缓存策略

建议 Caffeine 参数写清楚：

- `maximumSize(1000)`
- `expireAfterWrite(30 minutes)`
- `expireAfterAccess(10 minutes)`

不要在本任务中做过早优化，例如根据用户等级动态配置缓存大小。当前阶段只求稳定。

### Step 6: 运行工厂测试

执行：

```bash
mvn -Dtest=AiCodeGenServiceFactoryTest test
```

补一次手工验证：

1. 同一个 `appId + vue_project` 连续请求两次。
2. 确认命中同一个缓存键分支。
3. 切换到另一个 `appId` 或另一个 `codeGenType`。
4. 确认返回不同配置分支。

### Step 7: 记录和之前的区别

在任务记录中要写清楚：

- 之前是全局单例，现在是按 `appId + codeGenType` 缓存。
- 之前没有记忆，现在 `vue_project` 模式可以连续感知已经生成过的文件。
- 之前老模式和新模式会耦合，现在服务职责被拆开。

### Step 8: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java src/main/java/com/adcage/acaicodefree/core/memory/ChatMemoryLoader.java src/test/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactoryTest.java
git commit -m "feat: isolate ai services by app and mode"
```

## 验收标准

- `AiCodeGeneratorService` 已有 `generateVueProjectCodeStream()`。
- 工厂支持按 `appId + codeGenType` 获取服务。
- `vue_project` 模式挂载文件工具、专用模型和记忆。
- 老模式不依赖 Vue 工程工具。

## 风险说明

- 如果服务缓存和记忆加载耦合过深，后续会很难定位“是缓存问题还是上下文问题”。
- 如果把数据库查询逻辑继续塞在业务服务类里，后续第六阶段之后的逻辑会越来越难维护。

## 执行记录（2026-04-15）

- 状态：已完成
- 实际实现：`AiCodeGenServiceFactory` 从“统一单例 Service”调整为“按 `appId + codeGenType` 缓存 Service”；`vue_project` 分支挂载 `reasoningStreamingChatModel`、`FileWriteTool` 和 `ChatMemory`；新增 `ChatMemoryLoader` 从 `chat_history` 回放用户与 AI 历史消息构建窗口记忆。
- 关键差异：修改前不同应用和模式共享同一服务实例，容易导致上下文污染；修改后缓存键隔离明确，`vue_project` 多轮对话具备可延续上下文能力，老模式保留轻量链路。
- 验证结果：`mvn -Dtest=AiCodeGenServiceFactoryTest test` 通过；已纳入全量 `mvn test` 回归通过。
