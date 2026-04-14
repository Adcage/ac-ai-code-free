# Task 5 Stream Message Protocol And Facade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `vue_project` 模式建立统一的流消息协议，并让 `AiCodeGeneratorFacade` 正式分流到新的 TokenStream 适配链路。

**Architecture:** 这个任务解决的不是“前端怎么显示”，而是“后端流里到底传什么”。先把 AI 回复、工具请求、工具执行完成统一建模，再把 Facade 从旧的纯文本保存链路中拆出来，让 `vue_project` 模式具备独立的流协议出口。

**Tech Stack:** Reactor Flux, Java Model Classes, Facade Pattern, JSON Serialization

---

## Files

- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/AiResponseMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolRequestMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolExecutedMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessageTypeEnum.java`
- Modify: `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`
- Test: `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeStreamMessageTest.java`

## 当前问题

当前的流式结果只有一种语义：纯文本。

这导致三个后果：

- 前端无法区分 AI 说话还是工具执行。
- 后端无法基于消息类型做结构化处理。
- `vue_project` 模式只能假装自己还是老模式，最终又回到“整段文本拼接”的老路。

## 详细步骤

### Step 1: 先写流消息模型测试

测试目标是：给定一组模拟事件，可以产出稳定 JSON 字符串。

示例断言结构：

```java
@Test
void shouldSerializeAiResponseMessage() {}

@Test
void shouldSerializeToolRequestMessage() {}

@Test
void shouldSerializeToolExecutedMessage() {}

@Test
void facadeShouldRouteVueProjectToJsonMessageStream() {}
```

### Step 2: 新建消息模型类

字段建议保持最小必要集：

```java
public class StreamMessage {
    private String type;
}
```

```java
public class AiResponseMessage extends StreamMessage {
    private String data;
}
```

```java
public class ToolRequestMessage extends StreamMessage {
    private String id;
    private String name;
    private String arguments;
}
```

```java
public class ToolExecutedMessage extends StreamMessage {
    private String id;
    private String name;
    private String arguments;
    private String result;
}
```

注意：

- 这些模型类必须能被 JSON 序列化和反序列化。
- 必须保留无参构造，避免后续解析失败。

### Step 3: 新建消息类型枚举

枚举值固定为：

- `ai_response`
- `tool_request`
- `tool_executed`

不要在本任务里扩展“思考中”“计划中”等额外状态，先把第七阶段最小协议做稳。

### Step 4: 修改 `AiCodeGeneratorFacade`

当前逻辑：

- `SINGLE_FILE` -> 旧流
- `MULTI_FILE` -> 旧流
- 默认抛错

目标逻辑：

- `SINGLE_FILE` -> 原样走 `CodeFileSaverExecutor.executeSaverStream()`
- `MULTI_FILE` -> 原样走 `CodeFileSaverExecutor.executeSaverStream()`
- `VUE_PROJECT` -> 调 `generateVueProjectCodeStream(appId, userMessage)`，然后进入新的 JSON 消息适配链路

不要为了表面统一，强行让三种模式共用一套处理逻辑。第七阶段最重要的是分流明确。

### Step 5: 处理 TokenStream 适配策略

如果当前 LangChain4j 版本无法稳定拿到工具流回调，需要在计划中明确一个工程折中：

- 允许最小必要的兼容层。
- 只为拿到工具请求和工具执行完成事件服务。
- 不在本任务中顺手改造第三方库其他部分。

这个决定要在任务记录里写清楚，不要把兼容补丁伪装成“常规写法”。

### Step 6: 运行测试

执行：

```bash
mvn -Dtest=AiCodeGeneratorFacadeStreamMessageTest test
```

如果短期测试还没完全成型，至少要有一组手工构造消息的断言，确保 JSON 串格式稳定。

### Step 7: 手工验流

目标不是看前端，而是先看后端发出的 chunk 内容：

1. 触发一次 `vue_project` 生成。
2. 观察 `Flux<String>` 的输出。
3. 确认至少能看到 `ai_response` 和工具相关消息字符串。

### Step 8: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessage.java src/main/java/com/adcage/acaicodefree/ai/model/message/AiResponseMessage.java src/main/java/com/adcage/acaicodefree/ai/model/message/ToolRequestMessage.java src/main/java/com/adcage/acaicodefree/ai/model/message/ToolExecutedMessage.java src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessageTypeEnum.java src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeStreamMessageTest.java
git commit -m "feat: add vue project stream message protocol"
```

## 验收标准

- `vue_project` 模式不再复用老的纯文本保存链路。
- 统一消息模型类已经存在。
- Facade 可以按模式分流到正确处理分支。
- 输出 JSON 消息时类型字段稳定可识别。

## 风险说明

- 如果这一层没切干净，后续处理器、前端和落库都会被迫继续解析脆弱字符串。
- 如果过早往协议里塞更多消息类型，会把范围扩大到第八阶段之后。
