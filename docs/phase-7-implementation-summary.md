# Phase 7 Vue Project Generation 实施总结

## 文档目的

这份文档用于完整总结 Phase 7 的实施结果。它不是简单的“改了哪些文件”的清单，而是把这次阶段性交付真正做成了什么、每一块代码修改前后有什么差异、这些改动分别对应到哪一份任务文档、为什么必须这样做、最终带来了什么效果，系统地记录下来，便于后续继续迭代、回归排查、代码评审和阶段复盘。

对应总控文档：`docs/plans/2026-04-14-phase-7-vue-project-generation.md`

对应任务文档目录：`docs/plans/2026-04-14-phase-7-vue-project-generation/`

---

## 一、阶段目标与最终结果

### 1.1 阶段目标

Phase 7 的目标不是简单地增加一个新的枚举值 `vue_project`，而是把现有“生成网页代码片段”的链路升级成“生成完整 Vue 3 工程”的链路。这个目标包含几个必须同时成立的子目标：

1. 用户可以创建 `codeGenType=vue_project` 的应用。
2. AI 不再只吐一大段代码文本，而是能够以“逐文件写入”的方式生成项目文件。
3. 生成完的结果不是源码堆在那里，而是会自动执行安装依赖和构建，产出 `dist`。
4. 平台预览和部署看到的是构建后的页面，不是源码目录。
5. 用户在前端能够看到结构化进度，包括 AI 回复、工具请求、工具执行完成。
6. 聊天记录页面中保存的是用户能读懂的自然语言过程，而不是内部 JSON 协议。
7. 旧模式 `single_file` / `multi-file` 不被新链路破坏。
8. 最终要有自动化测试和真实链路验收，而不是“理论上可以工作”。

### 1.2 最终结果

本阶段最终已经完成以下结果：

1. `vue_project` 模式已经完整打通，从创建应用、聊天生成、工具写文件、自动构建、预览、部署到聊天记录展示都能闭环。
2. 前端和后端已经围绕统一 SSE 契约完成联动，前端可以展示结构化进度信息。
3. 真实模型链路已完成至少一次严格验收，验证了 `dist` 产物、预览地址、部署地址、聊天记录可读性和旧模式回归。
4. 针对真实链路暴露出来的问题，已经补上了对应代码修复和测试保护，而不是只在手工验收时“避开问题”。

换句话说，这一阶段的结果不是“支持了一个新模式”，而是把平台从“代码片段生成器”推进成了“最小可交付工程生成器”。

---

## 二、总控文档与任务文档关系

这次 Phase 7 的实施严格围绕总控文档和子任务文档推进。

总控文档：`docs/plans/2026-04-14-phase-7-vue-project-generation.md`

它负责定义：

1. 总目标是什么。
2. 任务依赖是什么。
3. 每个任务的边界是什么。
4. 哪些里程碑必须勾选。
5. 最终“阶段完成”要满足什么标准。

子任务文档分别承担具体子问题：

1. Task 1：依赖与配置基线
2. Task 2：模式入口、DTO 与 Prompt 资源
3. Task 3：模型 Bean、文件写入工具、目录规则
4. Task 4：AI Service 工厂与聊天记忆加载
5. Task 5：流消息协议与 Facade 适配
6. Task 6：流处理器与聊天记录落库
7. Task 7：构建、预览、部署
8. Task 8：前端 SSE 契约与接入说明
9. Task 9：测试、集成验证、阶段验收

本次总结会按照这些任务的逻辑顺序展开，而不是只按文件名罗列，这样更容易理解整条链路是怎样一步一步从旧架构演变出来的。

---

## 三、Task 1 到 Task 3：打通 `vue_project` 最小基础设施

对应任务文档：

1. `01-task-1-dependency-and-config-baseline.md`
2. `02-task-2-entrypoints-enum-dto-prompt.md`
3. `03-task-3-reasoning-model-and-file-write-tool.md`

### 3.1 修改前的问题

在这三个任务开始之前，代码库只有 `single_file` 和 `multi-file` 两种模式。问题不只是“少一个枚举值”，而是整条链路都围绕“返回文本结果，然后后处理解析落盘”这套模型建立：

1. 控制层创建应用时会把 `codeGenType` 硬编码成 `multi-file`。
2. 没有专门用于工程生成的 Prompt。
3. 没有专门用于工程生成的推理流模型配置。
4. 没有工具可以把 AI 的输出直接写进指定工程目录。
5. 没有统一约定 `vue_project_{appId}` 这种工程目录规则。

如果不先改这几项，后面的服务工厂、流消息协议、自动构建全都无从谈起。

### 3.2 具体修改内容

#### 3.2.1 打开 `vue_project` 入口

相关文件：

1. `src/main/java/com/adcage/acaicodefree/model/enums/CodeGenTypeEnum.java`
2. `src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java`
3. `src/main/java/com/adcage/acaicodefree/controller/AppController.java`

这里的核心变化是把 `vue_project` 从“文档里的概念”变成“接口层真正可传、可校验、可保存”的业务值。

修改前：

1. 请求里即使带了 `codeGenType`，控制器也不会真正按它处理。
2. 数据库里应用记录也不会稳定保存这个模式值。

修改后：

1. `AppAddRequest` 支持接收 `codeGenType`。
2. `CodeGenTypeEnum` 新增 `VUE_PROJECT`。
3. `AppController#addApp` 使用请求传入的模式，做显式校验并保存，不再硬编码成 `multi-file`。

这样做的原因是：如果入口层没有明确保存模式，后续所有分支逻辑都只能靠猜，服务层不可能知道当前应用到底应该走旧模式还是新模式。

#### 3.2.2 增加工程生成 Prompt

相关文件：

1. `src/main/resources/prompt/codegen-vue-project-system-prompt.txt`

这个 Prompt 不是随便写一份“生成 Vue 项目”的说明，而是针对工程场景做了约束：

1. 必须通过 `writeFile` 工具逐文件写入。
2. 技术栈固定为 Vue 3 + Vite + Vue Router 4 + JavaScript + 原生 CSS。
3. `vite.config.js` 必须使用 `base: './'`。
4. 路由必须使用 `createWebHashHistory()`。
5. 页面文案必须使用中文。
6. 不能生成 `node_modules`、`dist` 等冗余目录。
7. 必须尽量保证工程能直接安装和构建。
8. 后来在真实验收中继续补强了依赖版本限制：要求依赖使用可安装的稳定版本，禁止声明 `@vue/compiler-dom`。

这样做的原因是：工程生成比单文件输出更脆弱。模型一旦随意发挥，例如输出错误依赖、错误路由模式、错误资源基址，后端后面再怎么构建和部署都只是在处理一个结构错误的项目。

#### 3.2.3 增加专用模型与文件写入工具

相关文件：

1. `src/main/java/com/adcage/acaicodefree/config/ReasoningStreamingChatModelConfig.java`
2. `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`
3. `src/main/java/com/adcage/acaicodefree/constant/AppConstant.java`

`ReasoningStreamingChatModelConfig` 的作用是为 `vue_project` 提供一个专用流式模型 Bean，而不是复用旧的普通流式模型。原因是工程生成对推理质量和工具调用能力要求更高，需要单独的配置入口。

`FileWriteTool` 则是整个新链路的关键基础设施。它的职责不是简单地“写文件”，而是：

1. 只允许相对路径写入。
2. 根据 `appId` 自动定位到 `temp/code_output/vue_project_{appId}`。
3. 通过 `normalize()` 和根路径校验阻止路径穿越。
4. 自动创建父目录。
5. 用 UTF-8 覆盖写入。
6. 返回结果里只保留相对路径，不暴露绝对路径。

修改前的旧链路是“先输出整段文本，再由后处理解析为文件”；修改后则变成“AI 在生成过程中直接调用工具逐文件落盘”。

这一步为什么重要：因为工程生成场景下，单次返回一个超长 JSON 或大段多文件文本非常不稳定，逐文件写入不仅更符合 Agent + Tool 模式，也更容易在前端展示中间过程。

---

## 四、Task 4：AI Service 工厂重构与聊天记忆加载

对应任务文档：`04-task-4-service-factory-and-chat-memory.md`

### 4.1 修改前的问题

旧版 `AiCodeGenServiceFactory` 的核心问题不是“写法不优雅”，而是它从根上不适合工程生成场景：

1. 服务实例是全局共享的，不按应用隔离。
2. 没有把 `appId` 作为记忆边界。
3. 没有能力把已有聊天历史回放到新的会话服务实例里。

对于 `single_file` / `multi-file` 这种一次性生成场景，这种设计勉强可用；但对于 `vue_project` 这种“我要继续补文件、继续改文件、继续构建”的连续工程场景，这会导致：

1. 应用 A 的上下文污染应用 B。
2. 同一应用第二轮生成拿不到第一轮历史。
3. 模型无法基于先前写入过哪些文件继续工作。

### 4.2 具体修改内容

相关文件：

1. `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
2. `src/main/java/com/adcage/acaicodefree/core/memory/ChatMemoryLoader.java`

`AiCodeGenServiceFactory` 被改造成：

1. 使用 Caffeine 按 `appId + codeGenType` 做缓存。
2. 旧模式仍然走 legacy service。
3. `vue_project` 模式单独创建 service，挂上：
   - `reasoningStreamingChatModel`
   - `FileWriteTool`
   - `chatMemoryProvider`

这里后续又做了一个非常关键的真实链路修复：

修改前使用的是 `.chatMemory(chatMemoryLoader.load(appId))`，这在真实 `@MemoryId` 场景下会让 LangChain4j 内部取 `chatMemoryProvider` 时为空，从而抛出空指针。

修改后变成：

1. 使用 `.chatMemoryProvider(memoryId -> ...)`
2. 如果 `memoryId` 是 `Long`，就按当前 `memoryId` 加载
3. 否则退回当前 `appId`

这个差异很重要。前者是“把一个记忆对象塞进去”，后者是“按当前会话上下文动态提供记忆对象”。在真实运行时只有后者和 `@MemoryId` 的机制是对齐的。

`ChatMemoryLoader` 的职责是从 `chat_history` 表中把该应用的历史消息读出来，回放进 `MessageWindowChatMemory`。它把 user/ai 消息重新构造成模型可理解的历史上下文，从而实现多轮连续生成。

### 4.3 这样做的原因

之所以必须做这层重构，不是为了“技术上更规范”，而是因为 `vue_project` 的本质是一个连续迭代的项目工作流。没有记忆隔离和历史回放，模型根本不知道自己之前写过哪些文件、当前项目结构是什么、下一轮应该追加还是覆盖。

---

## 五、Task 5：流消息协议与 Facade 适配

对应任务文档：`05-task-5-stream-message-protocol-and-facade.md`

### 5.1 修改前的问题

旧版 `AiCodeGeneratorFacade` 只把流式输出看成“文本 chunk 流”。这种设计对旧模式够用，因为旧模式只需要把流式文本收完整后再解析保存。但对 `vue_project` 来说，这种方式有三个问题：

1. 无法区分普通文本和工具调用事件。
2. 前端无法知道“现在是 AI 在回复”还是“文件已经写好了”。
3. 聊天记录落库时只能保存原始协议字符串，不可读。

### 5.2 具体修改内容

相关文件：

1. `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`
2. `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessage.java`
3. `src/main/java/com/adcage/acaicodefree/ai/model/message/AiResponseMessage.java`
4. `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolRequestMessage.java`
5. `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolExecutedMessage.java`
6. `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessageTypeEnum.java`

新的 Facade 逻辑是：

1. `single_file` / `multi-file` 仍然返回普通文本流。
2. `vue_project` 走 `buildVueProjectMessageStream(...)`。
3. 这个方法内部订阅 `generateVueProjectCodeStream(...)` 的：
   - `onNext`：包装为 `AiResponseMessage`
   - `onToolExecuted`：先发 `ToolRequestMessage` 再发 `ToolExecutedMessage`
   - `onError`：向下游透传错误
   - `onComplete`：结束流

这一步的关键不是“封装几个 DTO”，而是把原来没有结构的字节流，变成具备业务语义的事件流。

### 5.3 这样做的原因

后面 Task 6、Task 8、Task 9 都依赖这一层语义分离：

1. 没有协议类型，前端无法展示不同状态。
2. 没有协议类型，历史落库无法转换成可读文本。
3. 没有协议类型，测试无法明确断言工具事件是否出现。

所以这一步本质上是在为整个新链路建立可观察性。

---

## 六、Task 6：流处理器与聊天记录落库改造

对应任务文档：`06-task-6-stream-handlers-and-history-persistence.md`

### 6.1 修改前的问题

旧版 `AppServiceImpl#chatToGenCode` 会直接把流式内容拼接起来，最后落库。这样做在旧模式里还能接受，但在 `vue_project` 模式里会产生两个严重问题：

1. 聊天记录会保存原始结构化 JSON，而不是人能读懂的话。
2. 工具请求和工具完成事件可能重复展示，用户看到的日志会很乱。

### 6.2 具体修改内容

相关文件：

1. `src/main/java/com/adcage/acaicodefree/core/handler/SimpleTextStreamHandler.java`
2. `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`
3. `src/main/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutor.java`
4. `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

`StreamHandlerExecutor` 负责按 `codeGenType` 选择不同处理器：

1. 旧模式走 `SimpleTextStreamHandler`
2. `vue_project` 走 `JsonMessageStreamHandler`

`JsonMessageStreamHandler` 的职责是：

1. 读取 JSON 消息
2. 把 `ai_response` 追加到可读文本缓存
3. 把 `tool_request` 转换成“准备写入文件 xxx”
4. 把 `tool_executed` 转换成“已写入文件 xxx”
5. 对同一个工具事件做去重，避免重复展示

`AppServiceImpl#chatToGenCode` 也被重构成一条清晰的流程：

1. 校验 `appId`、`sessionId`、`message`
2. 校验应用归属与会话归属
3. 先保存用户消息
4. 调 Facade 获取原始流
5. 用 `StreamHandlerExecutor` 把流转成“要返回给前端的流 + 要保存的可读消息”
6. 在 `doOnComplete` 中保存 AI 历史记录
7. 对 `vue_project` 在保存历史前自动调用构建服务
8. 如果构建失败，状态改成 `failed`，并把构建错误一起写入历史
9. 如果流本身报错，则在 `doOnError` 里落失败记录

### 6.3 这样做的原因

这个改造的根本目的，是把“流返回给谁看”和“历史落库给谁看”这两个问题分离开。

返回给前端的流需要保留结构化信息，便于界面实时渲染；落到数据库的历史则应该变成用户能理解的自然语言过程。两者不是同一种数据形态，不能再混用一个字符串。

---

## 七、Task 7：自动构建、预览与部署

对应任务文档：`07-task-7-build-preview-and-deploy.md`

### 7.1 修改前的问题

旧系统的预览和部署默认假设“生成目录就是可访问目录”，所以对 `single_file` 和 `multi-file` 可以直接暴露源码目录。但 `vue_project` 不是这样：

1. 源码目录不能直接作为最终预览结果。
2. 真正可访问的是构建后的 `dist`。
3. 部署如果复制源码目录，访问到的是源码文件而不是页面资源。

### 7.2 具体修改内容

相关文件：

1. `src/main/java/com/adcage/acaicodefree/core/build/VueProjectBuildService.java`
2. `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

`VueProjectBuildService` 提供了平台侧统一构建能力：

1. 根据 `appId` 找到 `temp/code_output/vue_project_{appId}`
2. 执行 `npm install`
3. 执行 `npm run build`
4. 校验 `dist` 是否存在
5. 在 Windows 环境下自动使用 `npm.cmd`
6. 对日志做长度裁剪，避免错误信息无限膨胀

后来在真实验收中，这个类又被进一步增强：

1. 识别 `npm install` 的 `ETARGET` 错误
2. 从错误信息中提取缺失的包和版本
3. 用 `npm view <package> version` 查询可用最新版本
4. 自动改写 `package.json` 中对应依赖版本
5. 必要时联动回退 `vue` 和 `@vue/compiler-sfc`
6. 再次执行 `npm install`

这不是“锦上添花”的优化，而是因为真实模型输出中出现了 `@vue/compiler-dom@3.5.30` 这种不可安装版本。没有这层自动修复，真实链路只能依赖模型刚好输出完全正确的依赖版本，风险过高。

`AppServiceImpl#deployApp` 的修改则体现为两个方面：

1. `vue_project` 部署时源目录改为 `dist`
2. 返回的部署地址不再是抽象 host，而是明确返回 `http://localhost:{port}/api/static/{deployKey}/index.html`

这个变更背后的原因很直接：

1. 复制 `dist` 才是部署页面，复制源码目录是错误部署。
2. 返回目录 URL 时，服务端未必总能自动映射欢迎页，真实验收里已经出现了 404；直接返回 `index.html` 才稳定。

### 7.3 结果差异

修改前：

1. `vue_project` 理论上能生成源码，但不能保证可构建。
2. 预览和部署指向错误目录。
3. 部署 URL 可能返回一个目录地址，真实访问存在 404 风险。

修改后：

1. 生成结束后平台自动尝试构建。
2. 预览稳定指向 `dist/index.html`。
3. 部署稳定复制 `dist`，返回可直接打开的页面 URL。

---

## 八、Task 8：前端 SSE 契约接入与预览路径切换

对应任务文档：`08-task-8-sse-contract-and-frontend-integration.md`

### 8.1 修改前的问题

前端原先默认认为 SSE 里只有纯文本，因此存在这些问题：

1. 无法区分 AI 回复和工具进度。
2. 首页创建应用时没有显式传 `codeGenType=vue_project`。
3. 预览地址默认沿用旧模式路径，不会指向 `dist/index.html`。

### 8.2 具体修改内容

相关文件：

1. `ac-ai-code-free-fronted/src/pages/HomePage.vue`
2. `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
3. `ac-ai-code-free-fronted/src/api/typings.d.ts`
4. `docs/learn/AI-CodeGen-Frontend-Implementation.md`

`HomePage.vue` 的修改看起来很小，但非常关键：新增显式传递 `codeGenType: 'vue_project'`。如果不传，后端就无法根据请求创建对应模式的应用。

`AppGeneratorPage.vue` 的核心改造是 SSE 双层解析：

1. 先解析外层 SSE 的 `data:{"d":"..."}`
2. 再根据 `d` 判断是否为结构化 JSON
3. 如果是 `ai_response`，就按 AI 回复追加
4. 如果是 `tool_request` / `tool_executed`，就渲染工具进度
5. 如果不是结构化 JSON，则按旧模式纯文本兼容处理

也就是说，新逻辑不是简单替换旧逻辑，而是在兼容旧模式前提下，扩展对新协议的识别。

同时，前端预览地址逻辑也做了模式分流：

1. 旧模式：`/static/{codeGenType}_{appId}/index.html`
2. `vue_project`：`/static/vue_project_{appId}/dist/index.html`

### 8.3 这样做的原因

如果只改后端协议、不改前端解析，用户看到的就只是一团碎片化 JSON，体验比旧版更差。前端这部分修改的核心价值不是“能显示更多信息”，而是让 `vue_project` 真正具备可用的生成体验。

---

## 九、Task 9：测试、真实验收与暴露问题后的补强修复

对应任务文档：`09-task-9-tests-integration-and-acceptance.md`

这是整个阶段最重要的收尾任务，因为很多关键问题并不是在编码时能直接看出来的，而是在真实链路里才暴露。

### 9.1 测试补齐

相关测试文件包括：

1. `src/test/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactoryTest.java`
2. `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeStreamMessageTest.java`
3. `src/test/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandlerTest.java`
4. `src/test/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutorTest.java`
5. `src/test/java/com/adcage/acaicodefree/core/build/VueProjectBuildServiceTest.java`
6. `src/test/java/com/adcage/acaicodefree/controller/AppChatE2ETest.java`
7. `ac-ai-code-free-fronted/tests/chat-flow.e2e.test.mjs`
8. `src/test/java/com/adcage/acaicodefree/core/CodeParserOldTest.java`

这些测试分别覆盖：

1. 服务工厂缓存键与分支逻辑
2. 新流消息协议是否产出正确结构
3. JSON 流处理器是否把协议转换为可读文本
4. 构建服务命令执行与异常处理
5. 控制层 SSE、历史落库、部署 URL
6. 前端到后端的 API 级端到端链路
7. 单文件解析对真实模型不规范输出的容错

### 9.2 真实验收中暴露出来并修复的问题

#### 9.2.1 `generateVueProjectCodeStream` 缺少 `@UserMessage`

文件：`src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`

现象：真实调用时直接报参数绑定错误，服务端流中断。

原因：LangChain4j 对 service 方法参数有明确注解要求，`userMessage` 没有被标记为用户消息。

修复：给 `String userMessage` 增加 `@UserMessage`。

效果：真实模型能够正确接收到用户输入。

#### 9.2.2 `chatMemoryProvider` 为空导致空指针

文件：`src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`

现象：真实 `vue_project` 流一开始就报空指针。

原因：使用 `.chatMemory(...)` 与 `@MemoryId` 机制不匹配，内部仍然会取 `chatMemoryProvider`。

修复：改成 `.chatMemoryProvider(memoryId -> ...)`。

效果：同一应用多轮生成的连续记忆真正生效。

#### 9.2.3 SSE 流异常导致前端 `terminated`

文件：`src/main/java/com/adcage/acaicodefree/controller/AppController.java`

现象：前端 E2E 在读取 `vue_project` SSE 时，Node `fetch` 报 `TypeError: terminated`。

原因：服务端一旦在流生成阶段抛异常，连接直接中断，没有可消费的错误降级内容。

修复：在控制层对流增加 `onErrorResume(...)`，把错误转成一段可发送的文本消息。

效果：前端不再因为后端异常直接掉连接，SSE 契约保持稳定。

#### 9.2.4 `npm install` 因 `ETARGET` 失败

文件：`src/main/java/com/adcage/acaicodefree/core/build/VueProjectBuildService.java`

现象：真实模型生成的 `package.json` 使用了不存在的版本 `@vue/compiler-dom@3.5.30`，导致 `npm install` 失败，`dist` 无法生成。

原因：模型输出依赖版本并不总是准确，即使 Prompt 已经约束，也不能假设它永远完全遵守。

修复：

1. 识别 `No matching version found for ...` 错误
2. 查询 npm registry 当前可用版本
3. 自动修复 `package.json`
4. 必要时联动修复 `vue`、`@vue/compiler-sfc`
5. 重新执行安装

效果：真实构建链路不再对模型版本精度过度敏感。

#### 9.2.5 部署 URL 返回目录导致真实访问 404

文件：`src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

现象：部署接口返回 URL 后，直接访问目录地址时出现 404。

原因：静态资源映射不保证目录地址自动映射到欢迎页，尤其是部署目录下的复制产物并不总有目录欢迎页行为。

修复：部署地址统一返回到 `index.html`，并自动带上 `server.port` 与 `context-path`。

效果：部署接口返回值可以直接访问，不再需要调用方拼接页面路径。

#### 9.2.6 单文件模式在真实模型输出下无法落盘

文件：`src/main/java/com/adcage/acaicodefree/core/CodeParserOld.java`

现象：`single_file` 真实生成时 SSE 看起来有大量 HTML 内容，但最终 `temp/code_output/single_file_{appId}/index.html` 不存在。

原因：旧解析器只认严格的 fenced code block；真实模型可能输出说明文字 + HTML，或者未闭合 ` ```html ` 代码块，导致解析失败。

修复：

1. 保留严格 fenced code block 优先解析
2. 新增 `<!DOCTYPE html>` fallback
3. 新增 `<html` fallback
4. 新增未闭合 ` ```html ` fallback，同时保证空块仍然报错，不破坏旧测试语义

效果：旧模式在真实模型轻微格式漂移下仍能正常落盘和预览。

### 9.3 真实链路严格验收最终结果

最终已经完成以下真实验收结果：

1. `vue_project` 真实生成触发了多次 `writeFile` 工具调用。
2. 生成目录下存在真实 `dist/index.html`。
3. 预览地址可访问：`/api/static/vue_project_{appId}/dist/index.html`
4. 部署地址可访问：`/api/static/{deployKey}/index.html`
5. 聊天记录页显示的是“准备写入文件/已写入文件/构建完成/构建失败”等可读消息，而不是 JSON 原文。
6. `single_file` 旧模式也已通过回归，能够生成并访问预览。

这意味着 Phase 7 不是停留在代码层面“实现过”，而是已经在真实运行环境中闭环验证过。

---

## 十、前端历史问题顺手修复的内容

相关文件：

1. `ac-ai-code-free-fronted/tsconfig.json`
2. `ac-ai-code-free-fronted/src/pages/HomePage.vue`
3. `ac-ai-code-free-fronted/src/pages/admin/AppAdminPage.vue`
4. `ac-ai-code-free-fronted/src/pages/app/AppEditPage.vue`
5. `ac-ai-code-free-fronted/src/pages/app/MyAppListPage.vue`

这些改动虽然不直接属于 `vue_project` 主功能，但它们是把前端校验跑通的必要条件：

1. `tsconfig.json` 把错误放在根层级的 `paths` 移除，避免类型系统配置异常。
2. 多个页面补上 `res.data?.data` 可空判定。
3. 分页页码自增逻辑改为对 `undefined` 安全处理。
4. 某些接口入参类型做了更稳妥的字符串转换。

这么做的原因不是“顺手优化”，而是如果 `npm run type-check` 和 `npm run build` 本身过不去，就没法证明本阶段的新改动是可交付状态。

---

## 十一、最终对应关系汇总

### 11.1 功能结果与任务文档对应

1. `vue_project` 模式入口打开
对应：Task 2

2. 专用 Prompt、模型和文件工具建立
对应：Task 3

3. 按 `appId + codeGenType` 隔离服务和记忆
对应：Task 4

4. 统一流消息协议落地
对应：Task 5

5. 聊天记录可读落库
对应：Task 6

6. 自动构建、预览、部署基于 `dist`
对应：Task 7

7. 前端协议兼容与工具进度展示
对应：Task 8

8. 单测、E2E、真实验收、链路补强
对应：Task 9

### 11.2 为什么这些修改必须同时成立

这次阶段之所以不能只完成其中一部分，是因为整个 `vue_project` 模式是一个串联链路：

1. 没有 Task 2，应用根本创建不出正确模式。
2. 没有 Task 3，模型没有工具和目录约束，工程无法落盘。
3. 没有 Task 4，连续生成没有记忆，第二轮就会失真。
4. 没有 Task 5，前后端都不知道每个流事件是什么意思。
5. 没有 Task 6，聊天历史会污染成 JSON 协议垃圾。
6. 没有 Task 7，生成后的工程不能真正上线使用。
7. 没有 Task 8，用户界面无法消费这条新链路。
8. 没有 Task 9，真实问题根本暴露不出来，阶段不能算完成。

所以这不是 9 个松散的小任务，而是一条必须首尾闭合的工程化升级链路。

---

## 十二、验收清单

- [x] 可以创建 `codeGenType=vue_project` 的应用。
- [x] AI 能按文件逐步生成 Vue 工程。
- [x] 前端能实时看到 AI 回复和工具调用进度。
- [x] 工具返回信息不泄露绝对路径。
- [x] 同一应用多轮生成具备连续记忆。
- [x] 生成完成后自动构建并产出 `dist`。
- [x] 预览地址可以直接访问 `dist/index.html`。
- [x] 部署复制的是 `dist` 目录。
- [x] 部署地址返回的是可直接访问的页面 URL。
- [x] 聊天记录保存的是可读文本。
- [x] `single_file` 旧模式仍能生成和预览。
- [x] `multi-file` 旧模式未被本阶段破坏。
- [x] 后端关键测试通过。
- [x] 前端类型检查与构建通过。
- [x] 前后端端到端测试通过。
- [x] 已完成真实模型链路的严格收尾验证。

---

## 十三、验证步骤

### 13.1 后端测试验证

执行：

```bash
mvn "-Dtest=CodeParserOldTest,AppChatE2ETest,VueProjectBuildServiceTest" test
```

验证目标：

1. 单文件解析 fallback 不破坏旧语义。
2. `vue_project` 控制层、SSE、历史落库与部署 URL 行为正确。
3. 构建服务对 `ETARGET` 具备自动修复能力。

### 13.2 前端校验验证

工作目录：`ac-ai-code-free-fronted/`

执行：

```bash
npm run type-check
npm run build
```

验证目标：

1. 前端类型系统正常。
2. 新增 SSE 契约适配没有破坏现有构建。

### 13.3 前后端端到端验证

工作目录：`ac-ai-code-free-fronted/`

执行：

```bash
npm run test:e2e:chat
```

验证目标：

1. `single_file` 链路通过。
2. `vue_project` 链路通过。
3. SSE 不会因为后端异常直接断流。
4. 历史查询、会话查询等配套接口正常。

### 13.4 真实严格验收验证

步骤：

1. 启动后端服务。
2. 创建一个 `codeGenType=vue_project` 的应用。
3. 发起一次最小工程生成请求。
4. 观察前端对话流，确认出现 AI 回复、工具调用进度。
5. 检查目录 `temp/code_output/vue_project_{appId}/dist/index.html` 是否存在。
6. 访问预览地址：

```text
http://127.0.0.1:{port}/api/static/vue_project_{appId}/dist/index.html
```

7. 调用部署接口。
8. 访问部署地址：

```text
http://localhost:{port}/api/static/{deployKey}/index.html
```

9. 打开聊天记录页，确认显示为可读文本。
10. 再跑一次 `single_file` 应用生成，确认旧模式可预览。

### 13.5 本次真实验收的已记录结果

本次严格验收的成功结果已经记录在总控文档和 Task 9 文档中，关键结果包括：

1. 真实 `vue_project` 生成成功。
2. 真实 `dist` 成功生成。
3. 真实预览地址成功访问。
4. 真实部署地址成功访问。
5. 旧模式成功回归。

---

## 十四、结论

本次 Phase 7 的核心价值，不是“多了一个生成模式”，而是把平台真正推进到了工程级代码生成阶段。整个链路已经从“用户创建应用”一路闭环到“真实页面可访问”，并且在真实验收中对暴露出来的问题完成了代码级修复和测试级固化。

从阶段交付标准看，Phase 7 已经满足完成定义。

从工程质量角度看，这次实现最大的价值在于没有停留在“功能大体可跑”，而是把真实链路中最容易出问题的部分，例如参数绑定、记忆注入、流异常、依赖版本漂移、部署 URL、旧模式解析容错，都补成了明确的代码逻辑和测试保护。

这意味着后续进入下一阶段时，Phase 7 不再是一个不稳定前提，而是一个已经验收通过的稳定基座。
