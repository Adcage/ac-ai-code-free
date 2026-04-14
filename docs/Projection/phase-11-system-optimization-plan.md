# 第十一阶段：系统优化与工程质量加固 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有 AI 应用生成平台已经具备“创建应用、对话生成代码、保存历史、部署预览、封面展示”等基础能力的前提下，系统性补齐第十一阶段的性能、实时性、安全性、稳定性、成本五大优化项，让平台从“功能可用”升级为“可承受并发、可观测、可防护、可控成本、体验更稳定”的工程化产品。

**Architecture:** 第十一阶段不再继续堆叠新的业务功能，而是围绕现有主链路做横向优化。整体采用“最小侵入、可逐项落地、优先改善主链路”的思路：后端通过多实例模型工厂、Redis 缓存、Redisson 限流、LangChain4j Guardrails、重试与工具调用上限控制等机制增强服务端；前端围绕 SSE 错误展示、实时预览一致性和状态反馈做配套改造；配置层通过模型拆分、环境变量化、缓存区域与限流参数分层管理实现可运维化。所有优化项都必须服务于当前仓库的真实结构，而不是脱离现状重新设计一套平台。

**Tech Stack:** Spring Boot 3.5.5, Java 21, LangChain4j 1.0.0-beta3, Reactor, MyBatis-Flex, Redis, Spring Cache, Redisson, Vue 3, TypeScript, Ant Design Vue, EventSource / SSE。

---

**关联文档**

- AI 执行提示词附录：`docs/Projection/phase-11-system-optimization-prompts.md`

## 1. 阶段定位

第七阶段解决的是“生成代码”，第八阶段解决的是“平台能力补全”，第九阶段解决的是“可视化修改”。第十一阶段要解决的不是再加一个用户看得见的新页面，而是处理一个更关键的问题：

**当平台开始承载更长对话、更复杂生成链路、更多用户并发访问时，如何让系统仍然稳定、快速、可控。**

这一阶段的重点不是“做功能演示”，而是把系统从教程式原型推进到可持续演进的工程状态。图片中提到的五个方向非常准确，对当前仓库也都成立：

- 性能优化：解决 AI 调用串行、热点接口重复读库、首页精选数据反复查询的问题。
- 实时性优化：解决用户看到 AI 回复结束，但 Vue 工程实际还没构建完成、预览滞后的体验断层。
- 安全性优化：解决 AI 对话接口可能被刷、SSE 异常难以呈现、Prompt 注入缺乏基础防护的问题。
- 稳定性优化：解决大模型偶发空响应、异常响应、工具循环调用失控等问题。
- 成本优化：解决所有场景都用高价模型、路由与生成不分层、长上下文滥用造成费用失控的问题。

第十一阶段的目标不是一次性引入所有“听起来高级”的机制，而是把这些能力按当前代码结构拆成可执行、可验证、可灰度上线的一整套改造方案。

## 2. 当前仓库基线与差距

在写计划之前，先严格以当前仓库为准确认基线，避免文档建立在错误假设上。

## 2.1 当前已经存在的基础

后端已有：

- `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
  已提供 `GET /app/chat/gen/code/stream` SSE 对话接口。
- `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
  已负责对话生成、历史落库、会话创建、分页查询等核心流程。
- `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`
  已把“AI 生成 + 保存代码文件”封装为统一入口。
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
  已通过 LangChain4j `AiServices.builder()` 创建 AI 服务。
- `src/main/resources/application.yml`
  已有 `langchain4j.open-ai.chat-model` 与 `streaming-chat-model` 的基础配置。
- `src/main/java/com/adcage/acaicodefree/exception/GlobalExceptionHandler.java`
  已有统一 JSON 异常处理器。
- `src/main/java/com/adcage/acaicodefree/common/ErrorCode.java`
  已定义基础错误码体系。
- `src/main/java/com/adcage/acaicodefree/constant/AppConstant.java`
  已定义代码输出目录、部署目录与部署域名。

前端已有：

- `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
  已通过 `EventSource` 消费 SSE，对话生成与预览同页完成。
- `ac-ai-code-free-fronted/src/request.ts`
  已有 Axios 全局响应拦截器，能处理未登录跳转。
- `ac-ai-code-free-fronted/src/api/appController.ts`
  已具备应用、对话、部署、历史、会话等接口封装。

## 2.2 当前最关键的结构性缺口

当前仓库能跑，但距离第十一阶段目标还有明显差距：

### 1. AI 模型实例是单 Bean 注入，缺少按场景拆分

`AiCodeGenServiceFactory` 当前直接注入：

- `ChatLanguageModel chatModel`
- `StreamingChatLanguageModel streamingChatLanguageModel`

这意味着：

- 没有“推理模型 / 普通流式模型 / 路由模型”的职责分离。
- 也没有每次调用获取独立模型实例的工厂化能力。
- 当前仓库里还没有智能路由服务，但第八阶段文档已经为它铺过设想，第十一阶段应顺手把模型配置层打好。

### 2. 没有 Redis、缓存、限流相关基建

当前仓库中：

- 没有 `@EnableCaching`
- 没有 `CacheManager`
- 没有 `spring.data.redis` 配置
- 没有 `Redisson` 依赖与配置
- 没有限流注解、切面、限流 key 生成规则

也就是说，性能优化和安全优化需要从基建开始补。

### 3. SSE 只有正常流式输出，缺少面向前端的业务错误事件

当前 `AppController#chatToGenCode()` 会输出：

- `meta`
- 默认消息事件
- `done`

但 `GlobalExceptionHandler` 只返回普通 JSON。对于浏览器侧 `EventSource` 而言，一旦接口在流式过程中抛错，前端几乎拿不到结构化业务错误信息，只会进入 `onerror`，体验非常粗糙。

### 4. 预览时机与代码生成完成时机存在体验缝隙

当前前端在 `startSSE()` 结束后调用 `updatePreview()`。如果后续扩展到 Vue 工程模式，实际构建、保存、生成 `dist` 与前端可访问之间可能有时间差。图片里提到的“AI 回复结束了，但预览还是旧页面或白屏”问题，在当前架构下完全可能出现。

### 5. 配置安全性存在明显隐患

当前本地配置文件中已经出现明文 API Key 的使用方式，这在开发阶段常见，但不能进入第十一阶段文档的正式方案。第十一阶段必须明确：

- 文档中所有密钥只允许用占位符或环境变量形式描述。
- 正式实施时必须把模型密钥、Redis 密码等移出仓库配置文件。

### 6. 主链路仍然缺少“异常输入防护”和“异常输出兜底”

当前仓库没有：

- Prompt 注入检测
- 超长输入拦截
- 恶意关键词检测
- 输出质量兜底
- 工具调用上限控制

这会让 AI 功能在边界场景下暴露出明显风险。

## 2.3 第十一阶段不应该做什么

为了保持工程聚焦，第十一阶段明确不做下面这些事：

- 不重写整套 AI 架构。
- 不引入完整服务网关或 API 网关体系。
- 不上消息队列、分布式链路追踪、服务网格这类远超当前阶段复杂度的系统。
- 不做完整的内容安全平台。
- 不把前端改造成复杂 IDE 或实时协同编辑器。

第十一阶段强调的是：**在当前单体后端 + Vue 前端 + LangChain4j 主架构下，把真正影响体验和风险的工程问题补齐。**

## 3. 第十一阶段总体目标拆解

第十一阶段建议拆成 5 条主线、2 条贯穿性约束：

### 主线一：性能优化

- 为不同 AI 任务拆分模型配置。
- 为生成链路提供独立模型实例，避免共享状态导致的并发问题。
- 为热点只读接口接入 Redis 缓存。

### 主线二：实时性优化

- 确保“用户看到 AI 生成结束”与“用户能立即预览到新页面”尽量一致。
- 尤其针对工程型输出，明确构建完成的时机与预览刷新策略。

### 主线三：安全性优化

- 给高成本 AI 接口补齐用户级 / IP 级限流。
- 让 SSE 能返回结构化错误。
- 为 Prompt 输入增加基础护栏。

### 主线四：稳定性优化

- 给模型调用补齐合理重试。
- 为异常 AI 输出提供兜底与再提示机制。
- 避免工具调用无限循环。

### 主线五：成本优化

- 根据场景区分模型。
- 降低路由、分类、摘要类任务的单次成本。
- 限制不必要的高 token 输出。

### 贯穿约束一：配置必须可运维

所有新增配置都要遵循：

- 分环境。
- 可覆盖。
- 不把密钥写死在仓库。
- 能看懂用途。

### 贯穿约束二：优化项必须可验证

每一项优化都要有明确的验证方式：

- 功能验证
- 压测或并发验证
- 前端交互验证
- 配置生效验证
- 失败场景验证

## 4. 总体架构图（文字版）

第十一阶段建议采用下面的逻辑分层：

1. 控制层
   `AppController` 继续作为 AI 对话入口，但要接入限流注解，并与 SSE 错误返回机制配合。

2. AI 服务装配层
   新增模型配置类、模型工厂、路由服务工厂，负责根据任务类型创建独立模型实例，而不是让业务类直接依赖单例模型。

3. AI 安全与稳定层
   由 Input Guardrails、Output Guardrails、模型级重试、工具调用上限共同组成。

4. 性能层
   由 Redis 缓存与热点接口缓存管理组成。

5. 实时性与预览层
   由“保存代码 -> 构建项目 -> SSE 完成 -> 前端刷新预览”的顺序控制组成。

6. 成本控制层
   由多模型配置、路由模型降级、最大 token 限制与后续统计埋点组成。

这 6 层不一定都形成独立模块，但文档和实现时必须把职责边界讲清楚，避免所有逻辑继续堆进 `AppServiceImpl`。

## 5. 性能优化

## 5.1 问题一：AI 并发调用与模型实例隔离

图片中的核心结论是正确的：在某些模型适配器或流式链路下，虽然表面上使用的是异步或流式接口，但底层仍可能存在串行瓶颈、共享状态或解析阶段阻塞，导致多个用户同时调用时吞吐明显下降。

对当前仓库而言，第十一阶段最现实的目标不是先证明某个底层库一定串行，而是：

- 不再假设默认注入的模型 Bean 天然适合高并发复用。
- 按职责拆分模型配置。
- 在服务创建时显式获取独立实例。

## 5.2 技术方案对比

### 方案 A：继续沿用默认单 Bean 注入

优点：

- 改动最小。
- 代码最少。

缺点：

- 模型职责混杂，后续很难做“生成 / 路由 / 推理”分层。
- 不利于隔离并发问题。
- 难以为不同任务设置不同 `maxTokens`、`temperature`、日志开关。

结论：不选。

### 方案 B：手写工厂类，每次 new 模型

优点：

- 实例隔离明确。
- 生命周期简单。

缺点：

- 会绕开 Spring 配置管理。
- 配置绑定、环境切换、依赖注入体验都变差。
- 维护成本高。

结论：不作为首选。

### 方案 C：Spring `@ConfigurationProperties` + `@Scope("prototype")` + 工厂获取 Bean

优点：

- 与当前 Spring Boot 栈天然兼容。
- 参数配置清晰，便于按模型职责拆分。
- 每次获取都是新实例，适合隔离调用上下文。
- 后续扩展模型供应商也比较自然。

缺点：

- 比当前简单注入多一层装配代码。
- 需要统一约束 Bean 命名，避免注入歧义。

结论：第十一阶段选择该方案。

## 5.3 最终技术决策

第十一阶段把模型配置明确拆成 3 类：

- `streaming-chat-model`：主代码生成流式模型，服务当前 SSE 主链路。
- `reasoning-streaming-chat-model`：给更复杂的推理、工程修改、多步工具调用场景预留。
- `routing-chat-model`：专门负责路由、分类、轻量判断，优先用更便宜模型。

实现层面的决策是：

- 新增独立配置类，不再完全依赖 starter 默认注入。
- 这些配置类使用 `@ConfigurationProperties` 绑定。
- 对模型 Bean 使用 `@Scope("prototype")`。
- 业务层不直接依赖原始模型 Bean，而是通过工厂或创建方法显式获取。
- 如果某些服务只需要普通分类，不允许复用高成本推理模型。

## 5.4 配置设计

建议在配置文件中采用下面这组结构，而不是把所有任务都塞在一个 `chat-model` 里：

```yaml
langchain4j:
  open-ai:
    streaming-chat-model:
      base-url: ${AI_STREAM_BASE_URL}
      api-key: ${AI_STREAM_API_KEY}
      model-name: ${AI_STREAM_MODEL}
      max-tokens: 8192
      temperature: 0.6
      log-requests: true
      log-responses: true
    reasoning-streaming-chat-model:
      base-url: ${AI_REASONING_BASE_URL}
      api-key: ${AI_REASONING_API_KEY}
      model-name: ${AI_REASONING_MODEL}
      max-tokens: 32768
      temperature: 0.1
      log-requests: true
      log-responses: true
    routing-chat-model:
      base-url: ${AI_ROUTING_BASE_URL}
      api-key: ${AI_ROUTING_API_KEY}
      model-name: ${AI_ROUTING_MODEL}
      max-tokens: 100
      temperature: 0.0
      log-requests: false
      log-responses: false
```

关键点：

- 路由模型必须低成本、低输出长度。
- 推理模型温度更低，保证稳定性。
- 主流式模型保持现有主链路兼容性。
- 正式文档只允许写 `${ENV_VAR}` 形式，不得出现真实密钥。

## 5.5 推荐新增 / 修改文件

建议新增：

- `src/main/java/com/adcage/acaicodefree/config/ai/StreamingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/config/ai/ReasoningStreamingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/config/ai/RoutingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`（改造）
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingServiceFactory.java`（如果第八阶段智能路由已继续推进）

建议修改：

- `src/main/resources/application.yml`
- `src/main/resources/application-local.yml`

## 5.6 验证要求

- 启动项目后能正确装配 3 类模型 Bean。
- 并发创建多个服务实例时，不发生 Bean 注入冲突。
- 路由任务日志中确认使用的是低成本模型配置。
- 代码生成主链路在改造后不回归。

## 5.7 问题二：Redis 缓存优化

图片里举的典型缓存场景是“精选应用分页列表”。这和当前仓库非常契合，因为：

- `POST /app/good/list/page/vo` 是典型热点只读接口。
- 数据更新频率低于访问频率。
- 同页参数组合重复率高。

## 5.8 缓存策略选择

### 推荐缓存场景

- `listGoodAppVOByPage`
- 后续可扩展到首页精选数据、公共榜单、非强实时推荐结果

### 不建议直接缓存的场景

- 带用户身份的“我的应用”列表
- 当前登录用户相关数据
- 会话历史、SSE 对话结果
- 容易受权限影响的数据

## 5.9 技术方案对比

### 方案 A：手写 RedisTemplate 缓存逻辑

优点：

- 控制粒度最大。

缺点：

- 样板代码多。
- 容易把缓存逻辑散落到业务代码中。
- 后续维护成本高。

结论：不作为第十一阶段首选。

### 方案 B：Spring Cache + Redis

优点：

- 与当前 Spring Boot 栈自然契合。
- 用注解即可描述热点缓存。
- 容易按 `cacheName` 管理 TTL。

缺点：

- 复杂缓存策略不如手写灵活。

结论：第十一阶段选择该方案。

## 5.10 Redis 缓存最终决策

- 使用 `spring-boot-starter-data-redis` 作为 Redis 集成基础。
- 使用 Spring Cache 注解方式接入。
- 在启动类开启 `@EnableCaching`。
- 自定义 `CacheManager`，显式控制序列化器与过期时间。
- 缓存 key 不直接拼接对象 `toString()`，而是使用稳定序列化 + 哈希。

## 5.11 缓存 key 设计

缓存 key 工具建议新增：

- `src/main/java/com/adcage/acaicodefree/utils/CacheKeyUtils.java`

设计原则：

- 入参对象先标准化 JSON 序列化。
- 再用 MD5 或其他短哈希生成稳定 key。
- key 前缀包含业务域，例如：`good_app_page:`。

原因：

- 避免 Redis key 过长。
- 避免对象默认 `toString()` 不稳定。
- 便于按业务前缀排查。

## 5.12 Redis 配置建议

推荐配置：

```yaml
spring:
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      database: ${REDIS_DB:0}
      password: ${REDIS_PASSWORD:}
      timeout: 3s
```

说明：

- 默认值只用于本地开发。
- 生产环境必须通过环境变量覆盖。
- 不要把真实密码写入仓库。

## 5.13 CacheManager 配置决策

建议新增：

- `src/main/java/com/adcage/acaicodefree/config/RedisCacheManagerConfig.java`

必须明确以下决策：

- key 使用字符串序列化。
- value 使用 JSON 序列化。
- 处理 Java 8 时间类型。
- 支持按缓存区域单独设置 TTL。

推荐缓存区域：

- `good_app_page`：5 分钟
- 后续可按需增加 `featured_app_detail` 等区域

## 5.14 缓存落点建议

优先在下面这个接口上落缓存：

- `AppController#listGoodAppVOByPage()`

原因：

- 流量稳定且集中。
- 精选内容不是强实时。
- 用户感知明显。

不建议第一批就缓存 Service 内部复杂方法，先从控制层 / 门面层入口验证更清晰。

## 5.15 缓存注意事项

- 不要缓存带登录态的数据。
- 不要缓存频繁写入的数据。
- 不要用默认 JDK 序列化，排查太差。
- 需要考虑空值策略，但第十一阶段先不引入复杂的 null-cache 与防击穿方案，避免过度设计。

## 6. 实时性优化

## 6.1 当前问题

图片中的问题描述与当前仓库高度一致：

- 用户看到 AI 内容流式输出已经完成。
- 但如果输出的是工程型项目，实际保存、构建、产物生成还没结束。
- 前端这时刷新预览，很可能还是旧页面、空页面或不完整页面。

这会造成非常糟糕的认知错位：用户以为“生成完了”，但系统实际还没到“可访问”状态。

## 6.2 技术方案对比

### 方案 A：保持异步构建，前端轮询构建状态

优点：

- 后端主请求返回更快。
- 构建过程可以脱离主链路。

缺点：

- 需要额外状态接口。
- 前端逻辑更复杂。
- 用户会经历“AI 已结束，但仍在等构建”的双阶段体验。

### 方案 B：异步构建 + SSE / WebSocket 推送构建状态

优点：

- 体验比轮询更实时。

缺点：

- 实现复杂度明显提高。
- 当前仓库没有额外实时状态通道基础。

### 方案 C：对主链路改为“先完成保存 / 构建，再发送完成事件”

优点：

- 用户认知最一致。
- 前后端逻辑最直观。
- 更适合当前单体架构。

缺点：

- 最终 `done` 事件会稍晚。

结论：第十一阶段主方案选择 C。

## 6.3 最终开发决策

对于工程型输出，建议把流程顺序固定为：

1. 模型流式输出结束。
2. 后端完成代码保存。
3. 后端完成必要的构建步骤。
4. 后端再发 `done`。
5. 前端在收到 `done` 后刷新预览。

这个决策的核心不是追求理论最优吞吐，而是保证用户体验一致性。

## 6.4 为什么本阶段不建议直接集成 Vite Dev Server

图片中已经分析过 Vite Dev Server 集成的路线，这里明确结论：

- 它确实可以带来近实时热更新体验。
- 但会引入每个应用单独 dev server、代理转发、端口分配、资源释放、WebSocket 转发等一系列复杂问题。

对当前仓库来说，这条路线明显超出了第十一阶段应承担的复杂度。第十一阶段只需要解决“结果与预览一致”，不需要把平台升级成在线 IDE。

## 6.5 当前仓库推荐落点

建议重点检查并改造：

- `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`
- 各代码保存器与构建触发位置
- `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`

前端改造目标：

- 不再把“模型停止输出”简单等同于“页面已可预览”。
- 只有收到 `done` 后才执行最终刷新。
- 若后续扩展状态事件，也要能优雅展示“保存中 / 构建中 / 可预览”。

## 6.6 可选扩展能力

第十一阶段文档保留两个扩展点，但不要求第一批必须实现：

- `GET /app/build/status/{appId}` 构建状态查询接口
- SSE 额外发送 `build-status` 事件

这两个扩展点可作为后续阶段增强，而不是第十一阶段上线阻塞项。

## 7. 安全性优化

## 7.1 流量保护：AI 对话接口限流

AI 对话接口是当前平台最昂贵、最容易被滥用的接口。第十一阶段必须优先保护：

- `GET /app/chat/gen/code/stream`

## 7.2 技术方案对比

### 方案 A：仅在前端做按钮节流

优点：

- 实现快。

缺点：

- 不能防脚本请求。
- 不能防刷接口。

结论：完全不够。

### 方案 B：本地内存限流

优点：

- 不依赖 Redis。

缺点：

- 单机重启丢状态。
- 后续扩容难处理。

结论：不作为正式方案。

### 方案 C：Redisson `RRateLimiter`

优点：

- 基于 Redis，天然适合共享限流状态。
- Java 侧接入简单。
- 支持令牌桶模型，表达力强。

缺点：

- 需要额外引入依赖与客户端配置。

结论：第十一阶段选择该方案。

## 7.3 限流最终决策

- 使用 Redisson + Redis。
- 基于令牌桶限流。
- 提供注解式接入，避免在控制器里手写重复逻辑。
- 支持三类维度：`API`、`USER`、`IP`。
- AI 对话接口默认采用 `USER` 限流，获取不到登录用户时降级为 `IP`。

## 7.4 推荐依赖与配置

`pom.xml` 建议新增：

- `org.springframework.boot:spring-boot-starter-data-redis`
- `org.redisson:redisson`

建议新增配置类：

- `src/main/java/com/adcage/acaicodefree/config/RedissonConfig.java`

建议新增限流相关目录：

- `src/main/java/com/adcage/acaicodefree/ratelimit/annotation/RateLimit.java`
- `src/main/java/com/adcage/acaicodefree/ratelimit/aspect/RateLimitAspect.java`
- `src/main/java/com/adcage/acaicodefree/ratelimit/enums/RateLimitType.java`

## 7.5 错误码与异常决策

`ErrorCode` 建议新增：

- `TOO_MANY_REQUEST(42900, "请求过于频繁")`

原因：

- 当前错误码里没有 429 语义。
- 限流异常不应该复用 `SYSTEM_ERROR` 或 `OPERATION_ERROR`。

## 7.6 限流 key 规则

限流 key 必须可预测、可定位、可区分业务。

建议规则：

- API 级：`rate_limit:api:{ClassName}.{methodName}`
- 用户级：`rate_limit:user:{userId}`
- IP 级：`rate_limit:ip:{clientIp}`

注意：

- 用户级拿不到用户信息时要自动降级为 IP 级，不能直接放行。
- IP 获取必须考虑 `X-Forwarded-For`、`X-Real-IP`、`remoteAddr` 的回退顺序。

## 7.7 推荐默认限流参数

第十一阶段建议从保守配置开始：

- AI 对话生成接口：每用户 60 秒最多 5 次
- 非登录态降级到 IP：每 IP 60 秒最多 3 次

这组参数偏保守，但更利于观察首轮上线效果。后续再根据实际使用数据调优。

## 7.8 SSE 业务错误返回机制

这是第十一阶段非常关键的一项配套优化。

### 当前问题

如果限流、参数校验或运行时异常出现在 SSE 链路中，前端 `EventSource` 很难拿到标准业务错误体，只能知道“连接出错了”。这对用户非常不友好。

### 最终决策

- `GlobalExceptionHandler` 必须识别 SSE 请求。
- 对普通 HTTP 请求，继续返回标准 JSON。
- 对 SSE 请求，写入自定义事件，而不是直接走 JSON 响应。
- 自定义事件名使用 `business-error`，避免与浏览器默认 `error` 事件语义冲突。

### 前端配套要求

在 `AppGeneratorPage.vue` 中必须新增：

- `eventSource.addEventListener('business-error', ...)`

收到该事件后要：

- 停止 loading
- 关闭流
- 将错误消息写入聊天区或提示条
- 避免只剩一个“网络错误”假象

## 7.9 Prompt 安全审查与护栏

图片里提到的 Guardrails 方案很适合当前仓库，因为它比自己造一套 Prompt 审核引擎轻量得多。

## 7.10 护栏边界定义

第十一阶段先做输入护栏，不追求复杂内容安全系统。

要拦截的内容包括：

- 超长输入
- 空输入
- 明显注入指令
- 明显越权诱导语句
- 明显恶意攻击表达

不在第十一阶段处理的内容：

- 高级语义级对抗识别
- 多轮上下文综合安全审计
- 图片内容安全
- 全链路内容审核工作台

## 7.11 技术决策

- 使用 LangChain4j `InputGuardrail`。
- 新增轻量类，例如：
  `src/main/java/com/adcage/acaicodefree/ai/guardrail/PromptSafetyInputGuardrail.java`
- 在 AI 服务构建阶段挂入，而不是在各控制器手写检查。

## 7.12 护栏规则建议

第一批规则建议非常克制：

- 长度上限：如 1000 或 2000 字符内
- 非空校验
- 关键词命中：如“忽略之前指令”“bypass”“jailbreak”等
- 正则注入模式：如伪装系统指令、要求泄露 prompt、要求忽略安全规则

注意：

- 这些规则只能做基础防护，不能夸大为完整安全能力。
- 拦截命中后的错误文案必须对用户友好，不要返回技术味过重的信息。

## 8. 稳定性优化

## 8.1 大模型重试策略

图片中将“重试策略 + 输出护栏 + 工具调用优化”作为稳定性主轴，这个判断正确。

第十一阶段稳定性优化的核心不是把所有异常都吞掉，而是：

- 对短暂失败自动重试。
- 对明显无效输出进行二次约束。
- 对无限工具循环及时熔断。

## 8.2 重试策略方案对比

### 方案 A：完全不重试

优点：

- 逻辑最简单。

缺点：

- 对临时失败容错极差。

### 方案 B：只依赖模型 SDK 或 starter 默认重试

优点：

- 实现简单。

缺点：

- 粒度有限。
- 不一定能覆盖响应内容质量问题。

### 方案 C：模型级重试 + Guardrail 再提示

优点：

- 能同时处理“请求失败”和“响应质量不达标”两类问题。

缺点：

- 需要非常谨慎地控制使用场景。

结论：采用 C，但按场景拆分使用强度。

## 8.3 重试最终决策

### 第一层：模型级重试

通过配置或 builder 明确设置：

- `max-retries: 2 ~ 3`

适用场景：

- 网络抖动
- 上游瞬时失败
- 非业务型超时

### 第二层：输出护栏

可新增：

- `src/main/java/com/adcage/acaicodefree/ai/guardrail/RetryOutputGuardrail.java`

用于处理：

- 空输出
- 极短无意义输出
- 命中敏感信息输出
- 不符合最低格式要求的响应

## 8.4 关于流式响应的关键决策

这一点必须明确写出来，不能含糊：

LangChain4j 的输出护栏在流式响应场景下，通常要等完整响应完成后才能判断是否重试或 reprompt。这意味着：

- 如果把 `reprompt` 型输出护栏直接用在主代码生成流式链路上，可能破坏“即时流式输出体验”。

所以第十一阶段建议：

- 对非流式、轻量、分类类、同步类任务优先启用 `OutputGuardrail`。
- 对当前主 SSE 代码生成链路，第一批只启用模型级 `max-retries` 与输入护栏。
- 主流式链路上的 `OutputGuardrail` 作为可选增强，不作为第一批上线阻塞项。

这是一个非常重要的工程决策，既尊重图片中的技术方向，也尊重当前仓库以流式体验为核心的现实。

## 8.5 工具调用优化

如果后续继续推进多文件工程修改、文件工具集、路由工具链等能力，工具调用失控会成为新的稳定性风险。

第十一阶段建议先把基础约束补上：

- 设置 `maxSequentialToolsInvocations`
- 限制单次 AI 调用内的工具连续调用上限
- 视需要引入退出工具 `ExitTool`

### 决策一：工具调用上限

若使用工具链服务，建议上限先从 10 到 20 次开始，不要无限制放开。

### 决策二：退出工具作为可选项

`ExitTool` 能让模型在完成任务后主动终止工具链循环，但它会增加一项心智负担，因此第十一阶段建议：

- 对复杂工程型多工具链服务可用。
- 对当前简单生成链路不强制接入。

## 9. 成本优化

## 9.1 成本优化原则

第十一阶段的成本优化不是单纯“换便宜模型”，而是：

- 让不同复杂度任务匹配不同成本级别的模型。
- 控制无意义的高 token 输出。
- 为后续统计和分析预留接口。

## 9.2 最终成本决策

### 决策一：路由模型必须独立且低成本

像代码生成类型判断、是否需要某种修改策略、简单分类这类任务，本质上是低复杂度分类问题，不应该复用主生成模型。

所以：

- `routing-chat-model` 必须与生成模型分离。
- `max-tokens` 必须显著更低。
- `temperature` 必须更低。

### 决策二：复杂生成与轻量判断分层

推荐模式：

- 生成类：中高质量流式模型
- 推理类：稳定型推理模型
- 路由类：廉价低 token 模型

### 决策三：文档中不锁死某一家模型厂商

图片里举了通义、DeepSeek 等供应商案例。第十一阶段正式文档不应该把系统绑死在某一家具体服务，而应该写成“兼容 OpenAI 协议的模型网关”。这样更符合当前 LangChain4j 接入方式，也更利于后续切换。

## 9.3 当前仓库推荐落地方式

在不改大架构的前提下，第十一阶段只要求先落 3 件事：

1. 配置层拆出低成本路由模型
2. 限制路由模型 `max-tokens`
3. 后续为 prompt 哈希缓存和调用统计预留扩展点

## 9.4 第十一阶段不强制但建议预留的成本能力

- 路由结果缓存
- Token 用量统计
- 用户 AI 调用次数统计
- 模型维度成本分析报表
- 老旧部署产物与 COS 文件的生命周期清理

## 10. 配置细节总表

第十一阶段建议新增或调整的配置项如下。

## 10.1 AI 模型配置

- `langchain4j.open-ai.streaming-chat-model.*`
- `langchain4j.open-ai.reasoning-streaming-chat-model.*`
- `langchain4j.open-ai.routing-chat-model.*`

## 10.2 Redis 配置

- `spring.data.redis.host`
- `spring.data.redis.port`
- `spring.data.redis.database`
- `spring.data.redis.password`
- `spring.data.redis.timeout`

## 10.3 缓存配置

- `cache.ttl.good-app-page=5m`
- 可选：`cache.ttl.featured-app-detail=5m`

如果不想引入自定义配置项，也可以全部在 `CacheManager` 里写死第一版 TTL，但推荐逐步抽配置。

## 10.4 限流配置

推荐新增自定义配置前缀：

```yaml
app:
  rate-limit:
    ai-chat:
      user-rate: 5
      user-interval-seconds: 60
      ip-rate: 3
      ip-interval-seconds: 60
```

说明：

- 第十一阶段可以先在注解里写死默认值。
- 如果计划长期运维，建议尽早抽成配置。

## 10.5 重试配置

- `langchain4j.open-ai.streaming-chat-model.max-retries`
- `langchain4j.open-ai.reasoning-streaming-chat-model.max-retries`
- `langchain4j.open-ai.routing-chat-model.max-retries`

## 10.6 密钥管理注意事项

第十一阶段文档必须明确：

- 示例配置一律使用环境变量占位符。
- 本地密钥不得继续作为正式方案写入仓库文档。
- 任何截图、示例代码、提示词中都不能复制真实 API Key。

## 11. 文件改造清单

本节给出推荐改造位置，供后续 AI 或开发者分批执行。

## 11.1 后端建议新增文件

- `src/main/java/com/adcage/acaicodefree/config/ai/StreamingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/config/ai/ReasoningStreamingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/config/ai/RoutingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/config/RedisCacheManagerConfig.java`
- `src/main/java/com/adcage/acaicodefree/config/RedissonConfig.java`
- `src/main/java/com/adcage/acaicodefree/utils/CacheKeyUtils.java`
- `src/main/java/com/adcage/acaicodefree/ratelimit/annotation/RateLimit.java`
- `src/main/java/com/adcage/acaicodefree/ratelimit/aspect/RateLimitAspect.java`
- `src/main/java/com/adcage/acaicodefree/ratelimit/enums/RateLimitType.java`
- `src/main/java/com/adcage/acaicodefree/ai/guardrail/PromptSafetyInputGuardrail.java`
- `src/main/java/com/adcage/acaicodefree/ai/guardrail/RetryOutputGuardrail.java`

## 11.2 后端建议修改文件

- `src/main/java/com/adcage/acaicodefree/AcAICodeFreeApplication.java`
  用于开启缓存。
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
  用于接入多模型、Guardrails、工具调用限制。
- `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
  用于对 AI SSE 接口增加限流注解。
- `src/main/java/com/adcage/acaicodefree/exception/GlobalExceptionHandler.java`
  用于识别 SSE 请求并写入 `business-error` 事件。
- `src/main/java/com/adcage/acaicodefree/common/ErrorCode.java`
  用于补充 429 限流错误码。
- `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`
  用于调整生成完成与构建完成的时序。
- `src/main/resources/application.yml`
- `src/main/resources/application-local.yml`
- `pom.xml`

## 11.3 前端建议修改文件

- `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
  用于处理 `business-error` SSE 事件、完善流结束状态、统一预览刷新时机。
- `ac-ai-code-free-fronted/src/request.ts`
  如果后续普通接口也返回 429，可统一提示节流信息。
- `ac-ai-code-free-fronted/src/api/appController.ts`
  若新增构建状态接口，需要补充 API 封装。

## 12. 开发任务拆分

本节给出推荐的实施顺序。由于用户明确说明业务或前端大块代码不必写进文档，所以这里重点写任务边界、改动目标和验收点，不粘贴大量实现代码。

### Task 1：整理 AI 模型配置并引入独立实例工厂

目标：

- 拆分流式生成模型、推理模型、路由模型。
- 让服务按需获取独立实例。

完成标准：

- 新配置可成功绑定。
- 主代码生成链路不回归。

### Task 2：引入 Redis 与 Spring Cache

目标：

- 完成 Redis 基础连接。
- 启用 `@EnableCaching`。
- 接入 `good_app_page` 缓存区域。

完成标准：

- Redis 中能看到缓存 key。
- 再次请求热点接口命中缓存。

### Task 3：统一预览完成时机

目标：

- 确保 `done` 事件只在最终可预览后触发。

完成标准：

- 用户收到 `done` 后刷新页面能看到最新结果。
- 不再出现“AI 回答结束但页面还是旧版”的明显问题。

### Task 4：接入 Redisson 限流

目标：

- 引入限流注解与切面。
- 先保护 AI SSE 接口。

完成标准：

- 高频触发时返回明确的限流错误。
- Redis 中能看到限流状态 key。

### Task 5：SSE 业务错误标准化

目标：

- `GlobalExceptionHandler` 识别 SSE 请求。
- 输出 `business-error` 自定义事件。
- 前端展示真实业务错误信息。

完成标准：

- 限流、参数错误在聊天区可见。
- 前端不会只显示模糊网络错误。

### Task 6：Prompt 输入护栏

目标：

- 基础拦截超长、空输入、注入型 prompt。

完成标准：

- 恶意输入能被拦截。
- 正常输入不被误伤。

### Task 7：模型重试与输出稳定性策略

目标：

- 给模型配置合理重试。
- 对非主流式链路接入输出护栏。

完成标准：

- 短暂异常时自动恢复能力增强。
- 不破坏当前主流式体验。

### Task 8：工具调用上限控制

目标：

- 为后续多工具链场景加保险丝。

完成标准：

- 工具循环不会无限持续。

### Task 9：路由模型成本分层

目标：

- 低复杂度任务切到低成本模型。

完成标准：

- 日志中可识别路由任务使用低成本模型。
- 主生成质量不受影响。

## 13. 测试与验证清单

## 13.1 后端验证

- 启动项目，确认 AI 模型配置绑定成功。
- 启动 Redis 后，确认缓存读写成功。
- 调用 `POST /app/good/list/page/vo` 两次，第二次命中缓存。
- 高频调用 `GET /app/chat/gen/code/stream`，验证限流触发。
- 构造 SSE 限流异常，确认前端收到 `business-error`。
- 构造恶意 prompt，确认 Guardrail 拦截。
- 人工模拟模型空响应或极短响应，验证重试策略是否按设计工作。

## 13.2 前端验证

- 正常对话时流式渲染不受影响。
- 触发限流后，页面展示明确提示，不只显示断流。
- 生成完成后预览刷新逻辑正确。
- loading 状态在异常与成功路径都能正确关闭。

## 13.3 并发验证

- 多浏览器或多账号同时发起生成请求。
- 观察是否出现明显串行阻塞。
- 验证是否存在共享上下文污染或响应错位。

## 13.4 配置验证

- 不同环境配置可以切换。
- 不依赖真实写死密钥。
- Redis、模型配置缺失时要能尽早失败并报出清晰信息。

## 14. 风险与注意事项

## 14.1 不要一次性把所有优化并到一个大提交里

第十一阶段内容多、横切面广。正确做法是分批推进：

1. 多模型配置
2. Redis 缓存
3. 实时性一致
4. 限流 + SSE 业务错误
5. Guardrails
6. 重试与工具调用优化
7. 成本分层

## 14.2 不能为了“加了优化”而破坏现有主链路

尤其要注意：

- 不要让缓存污染用户私有数据。
- 不要让输出护栏破坏主流式体验。
- 不要让限流误伤正常首轮用户。

## 14.3 不能继续把真实密钥写进文档或正式配置

这一条必须严格执行。

## 14.4 文档里的代码类名要以当前仓库为准

图片中的类名和当前仓库并不完全一致，例如当前仓库已经存在的是：

- `AiCodeGenServiceFactory`
- `AiCodeGeneratorFacade`
- `AppController`
- `GlobalExceptionHandler`

后续 AI 实施时必须优先改现有类，而不是照搬截图里不存在的类名。

## 14.5 业务代码与前端大段实现本计划不展开粘贴

这是有意为之。第十一阶段文档重点是：

- 技术选择
- 开发决策
- 配置细节
- 文件落点
- 验收方法

业务实现代码和前端细节会让文档暴涨且很快过时，因此只写必要接口、事件和约束。

## 15. AI 提示词附录

本节把原本独立拆出的 AI 提示词完整并回主文档，后续第十一阶段实施时只需要参考这一个文件即可。

## 15.1 使用原则

这一组提示词不是让 AI 一次性实现整份第十一阶段文档，而是让 AI 按任务分批、按边界、按验证目标执行。这样做的原因是：

- 第十一阶段横跨后端、前端、配置、缓存、限流、AI 模型装配多个层面。
- 一次性让 AI 改完整套系统，极易失控，且很难审查。
- 分任务提示能显著减少 AI 自行扩写、引入额外架构、修改无关文件的问题。

使用建议：

1. 每次只喂一个任务提示词。
2. 先让 AI 查现状，再做最小改动。
3. 每个任务完成后都要求 AI 说明验证结果。
4. 如果出现测试失败或行为异常，切换到调试提示词，不要继续堆功能。

## 15.2 总执行提示词

下面这段适合在开始实施第十一阶段任一子任务前使用。

```text
你正在 ac-ai-code-free 仓库中执行第十一阶段系统优化任务。请严格遵守以下要求：

1. 先阅读 `docs/Projection/phase-11-system-optimization-plan.md` 对应章节，再阅读当前仓库实际代码，确认计划中的类名、文件路径、接口名与现状一致。
2. 只实现当前任务范围内的内容，不要顺手重构无关模块，不要自作主张引入额外中间件或复杂架构。
3. 变更必须优先复用现有类和现有流程，例如 `AppController`、`AppServiceImpl`、`AiCodeGenServiceFactory`、`GlobalExceptionHandler`、`AppGeneratorPage.vue`。
4. 所有配置中的密钥必须使用占位符或环境变量，不允许写死真实值。
5. 完成后必须给出：改了哪些文件、为什么这样改、如何验证、还有哪些风险或未做项。
6. 如果发现文档和仓库现状不一致，以仓库现状为准，但要明确说明偏差点。

本次只执行当前任务，不要扩展到其他第十一阶段子任务。
```

## 15.3 Task 1 提示词：多模型配置与独立实例工厂

```text
请实现第十一阶段的“多模型配置与独立实例工厂”子任务。

目标：
- 将当前单一模型装配方式改造成按职责分层的模型配置。
- 至少支持：主流式生成模型、推理模型、低成本路由模型。
- 使用 Spring Boot 配置绑定和 prototype 作用域，避免直接共享同一模型实例。

执行要求：
- 先检查当前 `AiCodeGenServiceFactory`、`application.yml`、`application-local.yml` 的现状。
- 优先新增配置类，不要把所有逻辑继续堆在一个类里。
- 只改与模型装配相关的代码，不实现缓存、限流、SSE 错误处理等其他任务。
- 不能把真实 API Key 写进代码或配置文件。
- 如仓库当前还没有路由服务实现，也要先把路由模型配置和工厂准备好，但不要强行实现整个业务路由流程。

完成后请输出：
- 新增和修改的文件列表
- 模型职责划分说明
- 为什么选择 prototype + 工厂
- 如何验证装配成功
```

## 15.4 Task 2 提示词：Redis 缓存接入

```text
请实现第十一阶段的“Redis 缓存接入”子任务。

目标：
- 为当前仓库接入 Redis 与 Spring Cache。
- 先落一个真实有价值的热点缓存场景，优先考虑 `POST /app/good/list/page/vo`。
- 需要包含缓存 key 设计、CacheManager 配置、TTL 决策与序列化策略。

执行要求：
- 先检查当前 `pom.xml`、`AcAICodeFreeApplication`、`AppController` 是否已有 Redis 或缓存相关基础。
- 优先使用 Spring Cache 注解，不要在控制器里手写大量 RedisTemplate 读写逻辑。
- 缓存 key 不能直接用对象默认 `toString()`，必须稳定可控。
- 不要缓存登录态、权限敏感或强实时数据。
- 配置中使用环境变量，不写真实 Redis 密码。

完成后请输出：
- 缓存落点说明
- key 规则说明
- TTL 设置说明
- 如何在 Redis 中验证缓存命中
```

## 15.5 Task 3 提示词：生成完成与预览完成一致

```text
请实现第十一阶段的“生成完成与预览完成一致”子任务。

目标：
- 解决 AI 对话完成与用户可预览时间不一致的问题。
- 重点检查当前 `AiCodeGeneratorFacade` 与 `AppGeneratorPage.vue` 的联动。
- 确保前端收到真正完成信号后再刷新预览，而不是简单把模型停止输出视为完成。

执行要求：
- 先阅读当前 SSE 输出逻辑和前端 EventSource 消费逻辑。
- 优先采用对当前主链路侵入最小的方式，不要引入 Vite Dev Server 代理或全新 WebSocket 架构。
- 如果当前仓库还没有真正的 Vue 工程构建链路，也要把“完成时机的责任边界”理顺好，避免后续再返工。
- 不要顺便做限流和 Guardrails，这不是本任务范围。

完成后请输出：
- 后端完成时机如何判定
- 前端何时刷新预览
- 为什么不引入更重的实时预览方案
- 如何验证预览不再滞后
```

## 15.6 Task 4 提示词：Redisson 限流

```text
请实现第十一阶段的“Redisson 限流”子任务。

目标：
- 为 AI SSE 接口增加用户级 / IP 级限流能力。
- 使用 Redis + Redisson 的 RRateLimiter，不用本地内存限流。
- 通过注解 + AOP 接入，而不是在控制器中手写限流逻辑。

执行要求：
- 先检查当前仓库是否已有 Redis 相关配置，如果没有则补齐最小基础。
- 新增清晰的限流注解、限流类型枚举、AOP 切面。
- 默认优先用户级限流，拿不到用户时降级到 IP。
- 要补充明确的错误码，例如 429 语义错误码。
- 本任务只做后端限流与异常抛出，不负责前端 SSE 错误展示。

完成后请输出：
- 限流 key 规则
- 默认限流参数
- 使用注解的接口位置
- 如何验证限流生效
```

## 15.7 Task 5 提示词：SSE 业务错误展示

```text
请实现第十一阶段的“SSE 业务错误展示”子任务。

目标：
- 当 SSE 链路中出现业务异常时，让前端拿到结构化错误，而不是只有连接失败。
- 后端通过 `GlobalExceptionHandler` 或等价位置识别 SSE 请求并返回自定义事件。
- 前端 `AppGeneratorPage.vue` 监听该事件并展示友好错误提示。

执行要求：
- 先检查当前 `GlobalExceptionHandler` 和 `AppGeneratorPage.vue` 的 SSE 处理方式。
- 自定义事件名避免直接使用浏览器默认 `error`，推荐 `business-error`。
- 普通 JSON 接口行为不能被破坏。
- 需要同时处理业务异常和兜底运行时异常。
- 不要在本任务里顺手实现 Prompt Guardrails 或模型重试。

完成后请输出：
- SSE 错误事件格式
- 前端如何消费该事件
- 与普通 JSON 异常处理的分流逻辑
- 如何用限流或参数错误场景验证该功能
```

## 15.8 Task 6 提示词：Prompt 输入护栏

```text
请实现第十一阶段的“Prompt 输入护栏”子任务。

目标：
- 基于 LangChain4j InputGuardrail 为 AI 输入增加基础安全校验。
- 至少覆盖：空输入、超长输入、明显 Prompt 注入表达、明显恶意诱导表达。

执行要求：
- 先检查当前 AI 服务的创建位置和 LangChain4j 接入方式。
- 优先实现轻量、可维护的规则，不要尝试做复杂内容安全系统。
- 拦截提示文案要面向普通用户，不要过度技术化。
- 规则要尽量减少误伤，不要用过宽泛的关键词导致正常提示词经常被拦截。
- 本任务只实现输入护栏，不实现输出护栏或重试策略。

完成后请输出：
- 护栏规则清单
- 为什么规则边界定成这样
- 护栏挂载到哪里
- 如何验证命中与未命中场景
```

## 15.9 Task 7 提示词：模型重试与输出稳定性

```text
请实现第十一阶段的“模型重试与输出稳定性”子任务。

目标：
- 为 AI 模型调用增加合理的重试能力。
- 结合 LangChain4j OutputGuardrail 处理明显无效输出，但要注意流式场景的副作用。

执行要求：
- 先区分当前仓库的主流式代码生成场景与非流式轻量场景。
- 不要粗暴地把 reprompt 型 OutputGuardrail 直接加到当前主 SSE 代码生成链路上，否则可能破坏流式体验。
- 优先给非流式或轻量任务接入输出护栏，主流式链路优先使用模型级 max-retries。
- 需要明确写出你的场景边界与取舍理由。

完成后请输出：
- 哪些场景启用模型级重试
- 哪些场景启用 OutputGuardrail
- 为什么不直接把输出护栏全量用于流式生成
- 如何验证重试与护栏生效
```

## 15.10 Task 8 提示词：工具调用上限与退出工具

```text
请实现第十一阶段的“工具调用上限与退出工具”子任务。

目标：
- 为后续多工具调用场景加稳定性保险丝。
- 通过 `maxSequentialToolsInvocations` 或等价能力限制工具连续调用次数。
- 如仓库已有工具体系基础，可选引入 `ExitTool`；若当前没有成熟工具链，只实现上限控制即可。

执行要求：
- 先检查当前仓库是否已经有工具调用体系，如果没有，不要硬造复杂工具系统。
- 方案必须保持最小改动。
- 重点是防止无限循环，不是追求花哨能力。

完成后请输出：
- 当前仓库是否真的需要 ExitTool
- 最终设置的调用上限
- 为什么这样设置
- 如何验证不会再出现工具无限循环
```

## 15.11 Task 9 提示词：低成本路由模型

```text
请实现第十一阶段的“低成本路由模型”子任务。

目标：
- 为代码生成类型判断、分类、轻量决策场景接入低成本模型配置。
- 与主代码生成模型解耦。
- 控制输出 token 上限。

执行要求：
- 先检查当前仓库里是否已有路由服务；如果没有，只准备配置与工厂，不要硬造完整业务流程。
- 配置必须兼容当前 OpenAI 协议式接入方式。
- 不允许把主生成任务偷偷切成低成本模型导致质量回退。

完成后请输出：
- 路由任务与生成任务的模型职责分工
- 低成本模型配置项
- token 与温度控制策略
- 如何验证路由确实没有走主生成模型
```

## 15.12 调试提示词

当某个第十一阶段子任务出现异常时，使用下面这段提示词，而不是直接要求 AI“再试一次”。

```text
当前第十一阶段任务实现后出现异常。请你按调试模式处理，不要直接重写实现。

要求：
1. 先复述异常现象与触发条件。
2. 再定位最可能的根因，明确是配置问题、Bean 装配问题、SSE 协议问题、Redis 连接问题、前端事件处理问题还是逻辑顺序问题。
3. 只做最小必要修复，不扩大修改范围。
4. 修复后给出验证命令或验证步骤。
5. 如果存在多个可能根因，按概率从高到低列出，并优先验证最可能的一项。
```

## 15.13 代码审查提示词

下面这段适合在某个第十一阶段子任务完成后，让 AI 以审查者身份检查风险。

```text
请对刚完成的第十一阶段子任务做代码审查，重点找问题，不要先写总结。

请重点检查：
- 是否改动了与任务无关的文件
- 是否存在破坏现有主链路的回归风险
- 配置是否写入了真实密钥或不安全默认值
- 缓存是否误用于用户私有数据
- 限流是否可能误伤普通请求
- SSE 错误处理是否会影响普通 JSON 接口
- Guardrail 规则是否过宽导致误拦截
- 流式场景是否错误使用了 reprompt 型输出护栏

输出格式：
- 先按严重程度列 Findings
- 每条都给文件路径和原因
- 如果没有发现问题，再明确说明“未发现明确问题”，并补充残余风险
```

## 15.14 验收提示词

下面这段适合在一个子任务改完后，要求 AI 给出验收清单。

```text
请为当前第十一阶段子任务生成验收清单。

要求：
- 必须区分后端验证、前端验证、异常路径验证、配置验证
- 只写当前任务相关的验收项
- 每一项都要能实际操作，不要写空泛描述
- 如果需要命令，请给出具体命令
- 如果是 SSE 或前端交互验证，请说明应观察到的页面现象
```

## 15.15 禁止性提示

如果你要把任务交给 AI 实现，建议额外附上这一段，减少 AI 发散：

```text
禁止事项：
- 不要引入与当前任务无关的新框架
- 不要把多个第十一阶段子任务混在一起做
- 不要重命名大量现有类
- 不要顺手重构整个 `AppServiceImpl`
- 不要写死真实密钥、密码、Token
- 不要为了“更先进”而引入当前仓库根本承载不了的复杂方案
```

## 15.16 本节结论

第十一阶段最大的风险不是“做不出来”，而是 AI 在执行时过度发挥，把一个本来可以分批落地的系统优化任务扩展成大范围重构。

所以这组提示词的作用非常明确：

- 帮你把任务切小
- 帮你约束 AI 的改动边界
- 帮你在实现后快速验收与审查

后续如需真正进入代码实施，建议严格按主计划中的任务顺序，配合本节逐项执行。

## 16. 本阶段结论

第十一阶段不是锦上添花，而是当前仓库进入更高可用阶段前必须补的一次系统性治理。

本阶段最重要的不是“做了多少优化项”，而是形成下面这组工程化能力：

- 模型职责分层
- 热点接口缓存
- 生成完成与预览完成一致
- AI 接口可限流、可报错、可防护
- 模型调用可重试、可控工具调用次数
- 路由类任务成本显著下降

只要这五条主线按本计划落地，第十一阶段就不是抽象的“系统优化”，而是对当前平台质量的一次明确升级。
