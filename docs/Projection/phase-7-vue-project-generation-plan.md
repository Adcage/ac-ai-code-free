# 第七阶段：Vue 工程项目生成 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有 `single_file` / `multi-file` 代码生成能力之上，新增 `vue_project` 工程生成模式，让 AI 能直接生成可安装、可构建、可预览、可部署的 Vue 3 工程，并把 AI 回复、工具调用请求、工具执行结果以流式方式稳定展示给前端。

**Architecture:** 后端继续使用 Spring Boot + LangChain4j + Reactor Flux 作为生成主链路。第七阶段引入独立的推理流模型、基于 `appId` 绑定的文件写入工具、按 `appId + codeGenType` 隔离的 AI Service 工厂、统一 JSON 流消息协议，以及面向不同生成模式的流处理器。Vue 工程模式不再走“整段文本输出后再解析落盘”的老链路，而是由 AI 直接调用工具逐文件写入 `temp/code_output/vue_project_{appId}`，生成结束后由后端固定执行 `npm install`、`npm run build`，再复用现有静态映射和部署目录完成预览与部署。

**Tech Stack:** Spring Boot 3.5.5, Java 21, LangChain4j, Reactor Flux, Hutool, MyBatis-Flex, Caffeine, Spring Data Redis（或等价会话记忆存储实现）, Vue 3, Vue Router 4, Vite, Node.js `^20.19.0 || >=22.12.0`。

---

## 1. 阶段定位

第七阶段不是再做一个“更多文件”的代码生成器，而是把平台从“生成网页代码片段”推进到“生成完整前端工程”。

现有仓库已经具备这些基础能力：

- `single_file`：生成单个 HTML 文件。
- `multi-file`：生成 `index.html + style.css + script.js`。
- `AiCodeGeneratorFacade`：统一生成入口。
- `CodeFileSaverExecutor`：对老模式做流式文本拼接、最终解析、最终落盘。
- `AppController#chatToGenCode`：通过 SSE 把 `Flux<String>` 推给前端。
- `WebMvcConfig`：把 `temp/code_output` 和 `temp/code_deploy` 暴露为 `/static/**`。

但这些能力还不够支撑“工程项目生成”：

- 现有模式本质上还是“让模型一次性吐出代码文本”，再由后端解析保存。
- 当前流式接口只能稳定处理纯文本，不适合展示“AI 正在创建哪个文件”。
- 当前 `AiCodeGenServiceFactory` 只生成一个全局 AI Service，没有做到按应用隔离记忆。
- 当前 `AppController#addApp` 仍然把 `codeGenType` 硬编码为 `multi-file`。
- 当前部署逻辑只是把源码目录拷贝到部署目录，没有执行 `npm install` / `npm run build`，所以无法稳定部署 Vite 工程。

第七阶段的目标，就是把这些缺口一次补上。

## 2. 本阶段范围与非目标

### 2.1 本阶段必须交付的内容

- 新增 `vue_project` 生成模式。
- 新增专用系统提示词资源。
- 新增文件写入工具，让模型逐文件落盘。
- 新增按 `appId + codeGenType` 隔离的 AI Service 构建策略。
- 新增聊天记忆绑定，让多轮生成时模型知道已经生成过哪些文件。
- 新增统一流消息协议，区分 AI 回复、工具调用请求、工具执行结果。
- 新增 Vue 工程专用的流处理器，保证前端展示和数据库落库都可读。
- 新增工程构建步骤，固定执行 `npm install` 和 `npm run build`。
- 调整预览与部署逻辑，让 `vue_project` 使用 `dist` 目录而不是源码目录。
- 补齐测试、验证清单、配置说明、风险说明。

### 2.2 本阶段明确不做的内容

- 不在本计划里写业务页面的完整 Vue 代码。
- 不要求第七阶段就把生成项目升级到 TypeScript、Pinia、Ant Design Vue。
- 不要求第七阶段就实现复杂工作流编排引擎。
- 不要求第七阶段就把“深度思考”可视化做成完整产品功能。

上面这些内容不是不能做，而是会显著扩大范围。第七阶段先把“工程生成主链路”做稳。

## 3. 技术选型与开发决策

## 3.1 方案对比

### 方案 A：直接输出 Markdown，多代码块后处理

做法：让模型把整个 Vue 项目按 Markdown 代码块输出，后端再解析每个文件。

优点：

- 实现最简单。
- 模型输出一眼能看懂。
- 与当前 `multi-file` 模式最接近。

缺点：

- 工程一大，输出极容易被截断。
- 一旦中途生成失败，恢复成本高。
- 实时展示时只能看到“长文本”，看不到 AI 正在操作哪个文件。
- 解析器要承担更多脆弱逻辑，鲁棒性差。

结论：不选。这个方案适合 demo，不适合工程模式。

### 方案 B：工具调用，由 AI 逐文件写入

做法：给 AI 提供 `writeFile` 工具，模型自己决定何时创建 / 覆盖哪个文件，后端负责把工具调用转换成真实文件系统操作。

优点：

- 文件落盘是增量的，不依赖一次性吐完全部代码。
- 用户可以实时看到 AI 正在写哪个文件。
- 更接近真实开发过程。
- 和后续 Agent 化演进兼容。

缺点：

- 流式展示会复杂很多，需要处理“工具调用请求的部分参数”“工具执行完成结果”“AI 自然语言回复”三类信息。
- 需要处理上下文记忆，否则模型容易重复生成同一个文件。
- 需要处理工具幻觉和参数异常。

结论：选这个方案。第七阶段的主方案就是“工具调用 + 流式展示”。

### 方案 C：完整 Agent，多步骤规划 + 多轮执行

做法：让模型先给出完整计划，再逐步骤执行，每一步都可能继续决定调用工具。

优点：

- 过程更清晰。
- 中断恢复能力更强。
- 适合复杂网站或多页面工程。

缺点：

- 架构复杂度明显上升。
- 调试成本高。
- 如果底层工具流式链路还不稳，Agent 只会放大不稳定性。

结论：不作为第七阶段主交付。第七阶段先把“工具调用能力”和“流式展示能力”打稳，再向 Agent 演进。

## 3.2 最终技术决策

第七阶段采用下面这组决策，不留模糊空间：

- 生成模式新增 `vue_project`，字符串值固定为 `vue_project`。
- Vue 工程模式采用“工具调用写文件”，不再走“整段文本输出后统一解析落盘”。
- Vue 工程模式使用独立的推理流模型，不和旧的普通流模型混用。
- AI Service 按 `appId + codeGenType` 维度缓存，不再是一个全局实例通吃所有场景。
- 记忆绑定使用 `appId` 作为 `@MemoryId`，确保同一应用多轮生成时上下文连续。
- 文件写入工具只允许写相对路径，并且只返回相对路径，绝不把服务器绝对路径暴露给模型和前端。
- 前端流展示采用统一 JSON 消息协议，不再把所有内容都当普通字符串。
- 数据库存储保存“用户可读的会话文本”，不直接保存原始 JSON 流消息。
- 构建步骤不交给 AI 决定，固定由后端程序在生成结束后执行 `npm install` 和 `npm run build`。
- 预览和部署都基于 `dist` 目录，不基于源码目录。
- 路由统一使用 Hash 模式，Vite `base` 强制为 `./`，确保子路径预览和部署稳定。
- 生成项目默认不引入 UI 框架、状态管理库、CSS 框架和 TypeScript，先追求稳定可生成、稳定可运行。

## 3.3 为什么不直接复刻主站前端技术栈

当前仓库前端 `ac-ai-code-free-fronted/package.json` 使用的是 Vue 3.5、Vue Router 4.5、Vite 7、TypeScript、Ant Design Vue 等完整栈。第七阶段不建议让 AI 直接生成这一整套技术体系，原因很简单：

- 依赖越多，模型越容易生成不完整配置。
- TypeScript、UI 框架、样式体系一起上，会把第七阶段的主要风险从“工程生成链路”转移成“前端业务代码质量”。
- 我们当前真正需要验证的是：工具调用、项目生成、流式消息、记忆、构建、部署，这些基础设施是否跑得稳。

所以第七阶段的生成项目建议控制在这条技术基线：

- Vue 3。
- Vue Router 4。
- Vite。
- 原生 CSS。
- 纯 JavaScript。

这条基线足够工程化，也足够稳定。

## 4. 目标架构

## 4.1 生成主链路

完整链路建议固定为：

1. 用户发送生成请求。
2. 服务端根据 `appId` 和 `codeGenType` 获取对应 AI Service。
3. `vue_project` 模式调用专用的 `generateVueProjectCodeStream()`。
4. 模型输出普通回复，并多次调用 `writeFile` 工具。
5. 后端监听 TokenStream，把 AI 回复、工具请求、工具执行结果转换成统一 JSON 消息。
6. 流处理器把这些 JSON 消息转换成：
   - 面向前端的实时展示片段。
   - 面向数据库的可读会话文本。
7. 生成完成后，由后端固定执行：
   - `npm install`
   - `npm run build`
8. 构建成功后得到 `dist` 目录。
9. 预览使用 `/api/static/vue_project_{appId}/dist/index.html`。
10. 部署时复制 `dist` 到 `temp/code_deploy/{deployKey}`。

## 4.2 目录约定

服务端目录约定固定如下：

- 源码根目录：`temp/code_output/vue_project_{appId}`
- 构建产物目录：`temp/code_output/vue_project_{appId}/dist`
- 部署目录：`temp/code_deploy/{deployKey}`

这个约定必须写死在工具实现、构建服务、预览路径和部署逻辑里，不能让模型自由决定。

## 4.3 后端模块分层建议

建议把第七阶段新增能力拆成 6 层：

- 模型层：`AiCodeGeneratorService` 新增 `vue_project` 专用方法。
- 配置层：新增推理模型配置类。
- 工具层：新增 `FileWriteTool`。
- 工厂层：重构 `AiCodeGenServiceFactory`，按模式和 appId 创建服务。
- 流协议层：新增 `StreamMessage` 及其子类。
- 流处理层：新增 `JsonMessageStreamHandler`、`SimpleTextStreamHandler`、`StreamHandlerExecutor`。

## 5. 需要修改和新增的文件

## 5.1 现有文件

- `pom.xml`
- `src/main/resources/application.yml`
- `src/main/java/com/adcage/acaicodefree/model/enums/CodeGenTypeEnum.java`
- `src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java`
- `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
- `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`
- `src/main/java/com/adcage/acaicodefree/constant/AppConstant.java`
- `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeTest.java`

## 5.2 新增文件

- `src/main/java/com/adcage/acaicodefree/config/ReasoningStreamingChatModelConfig.java`
- `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`
- `src/main/java/com/adcage/acaicodefree/core/memory/ChatMemoryLoader.java`
- `src/main/java/com/adcage/acaicodefree/core/build/VueProjectBuildService.java`
- `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessage.java`
- `src/main/java/com/adcage/acaicodefree/ai/model/message/AiResponseMessage.java`
- `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolRequestMessage.java`
- `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolExecutedMessage.java`
- `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessageTypeEnum.java`
- `src/main/java/com/adcage/acaicodefree/core/handler/SimpleTextStreamHandler.java`
- `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`
- `src/main/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutor.java`
- `src/main/resources/prompt/codegen-vue-project-system-prompt.txt`

如果最终决定采用“复制 LangChain4j 源码做临时增强”的兼容方案，还会新增最小必要的覆盖类到 `src/main/java/dev/langchain4j/...`。这个属于有意识的临时补丁，不是常规做法。

## 6. 配置细节

## 6.1 Maven 依赖调整

当前仓库使用的是 `langchain4j 1.0.0-beta3`。第七阶段建议升级到同一主版本线的稳定版本，并且所有 LangChain4j 相关依赖必须保持一致版本，不能混搭。

建议依赖调整方向：

- `dev.langchain4j:langchain4j`
- `dev.langchain4j:langchain4j-open-ai-spring-boot-starter`
- `dev.langchain4j:langchain4j-reactor`
- 新增 `com.github.ben-manes.caffeine:caffeine`
- 新增 `org.springframework.boot:spring-boot-starter-data-redis`

这里的重点不是“多加依赖”，而是解决 3 个问题：

- 工具调用和流式处理能力要够新。
- 服务缓存要可控。
- 聊天记忆要能脱离单 JVM 进程存储。

## 6.2 application.yml 调整

当前 `application.yml` 已经配置了普通 `chat-model` 和 `streaming-chat-model`。第七阶段要加一层明确约束：

- 原有普通模式继续沿用默认流式模型。
- `vue_project` 模式走独立 Bean，不直接复用 starter 自动生成的 Bean。

建议新增配置思路：

```yml
langchain4j:
  open-ai:
    chat-model:
      base-url: https://api.deepseek.com
      api-key: ${DEEPSEEK_API_KEY}
      model-name: deepseek-chat
      log-requests: true
      log-responses: true
      max-tokens: 8192
    streaming-chat-model:
      base-url: https://api.deepseek.com
      api-key: ${DEEPSEEK_API_KEY}
      model-name: deepseek-chat
      log-requests: true
      log-responses: true
      max-tokens: 8192

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

注意两点：

- `vue_project` 专用模型不要强行加 `response-format: json` 和 `strict-json-schema: true`。工具调用和自然语言说明并不是严格 JSON 输出场景。
- 开发环境优先用 `deepseek-chat` 降低成本、提升调试速度；生产环境再切 `deepseek-reasoner` 做更强规划和工具选择。

## 6.3 推理模型 Bean 的配置原则

建议新增 `ReasoningStreamingChatModelConfig`，明确创建一个命名清晰的专用 Bean，例如 `reasoningStreamingChatModel`。原因是当前仓库已经有 starter 注入的流式模型，名称不能混淆。

配置原则：

- Bean 名字明确，不和默认 `StreamingChatLanguageModel` 冲突。
- 单独读取 `app.ai.vue-project.*` 这一组配置。
- 支持开发 / 生产切换。
- 开启请求和响应日志，便于调试工具调用。

## 6.4 Node 与 Vite 配置决策

图片中的旧方案使用的是 Node 18+、Vue 3.3、Vite 4.4。这一组版本可以工作，但本仓库建议与当前前端环境更接近：

- Node.js：`^20.19.0 || >=22.12.0`
- Vue：`^3.5.x`
- Vue Router：`^4.5.x`
- Vite：`^7.x`
- `@vitejs/plugin-vue`：`^6.x`

如果模型在新版本依赖上稳定性不足，再回退到更保守的 `Vue 3.3 + Router 4.2 + Vite 4.4` 组合。这个回退路径要在文档里写清楚，但默认实施建议先对齐当前仓库环境。

## 7. 写给 AI 的系统提示词

下面这份提示词是第七阶段建议直接落到 `src/main/resources/prompt/codegen-vue-project-system-prompt.txt` 的版本。它刻意写得比较严格，因为这个场景容错空间很小。

```text
你是一位资深的 Vue 3 工程化开发专家，擅长用最少的依赖搭建完整、可运行、可构建、可部署的前端项目。

你的任务是根据用户的需求，为其创建一个完整的 Vue 工程项目。你必须优先保证项目可以运行、可以构建、目录结构清晰，而不是追求花哨的实现。

你的核心目标：
1. 生成一个可执行的 Vue 3 + Vite 项目。
2. 所有文件必须通过 writeFile 工具逐个创建或覆盖。
3. 不能把完整文件代码直接输出在普通文本里。
4. 项目生成结束时，必须确保结构完整，关键配置正确。

必须遵守的技术栈：
- Vue 3
- Vite
- Vue Router 4
- JavaScript
- 原生 CSS
- Node.js ^20.19.0 || >=22.12.0

默认不要引入：
- TypeScript
- Pinia
- Ant Design Vue
- Element Plus
- Tailwind CSS
- 任意额外 UI 框架
- 任意额外图标库

只有当用户明确要求，并且需求无法通过当前基线实现时，才可以额外加依赖。

项目结构要求：
- index.html
- package.json
- vite.config.js
- src/main.js
- src/App.vue
- src/router/index.js
- src/pages/
- src/components/
- src/styles/
- src/assets/（如确有必要）
- public/（如确有必要）

强制配置要求：
1. vite.config.js 中必须设置 base 为 './'。
2. vite.config.js 中必须设置 '@' 指向 './src'。
3. 路由必须使用 createWebHashHistory()。
4. index.html 必须加载 src/main.js。
5. package.json 必须包含 dev、build、preview 三个脚本。
6. 项目必须能在子路径下访问，不能依赖根路径部署。

页面与内容要求：
1. 页面内容必须使用中文。
2. 页面至少包含首页级主视图，且内容不能空洞。
3. 如果需求中有多个模块，优先拆到 pages 和 components 中。
4. 如果用户没有提供真实图片，可以使用占位图。
5. 如果用户没有提供真实数据，可以使用有意义的模拟数据。
6. 样式必须响应式，桌面端和移动端都要可用。

工程实现要求：
1. 组件优先使用 <script setup>。
2. 样式优先使用原生 CSS，不要额外引入 CSS 预处理器。
3. 代码命名清晰，目录结构清晰。
4. 不要生成无用文件。
5. 不要生成 node_modules、dist、README、截图、说明文档。

工具使用规则：
1. 每个文件必须通过 writeFile(relativeFilePath, content) 写入。
2. relativeFilePath 必须是相对路径，不能是绝对路径。
3. 如果需要修改某个文件，直接再次调用 writeFile 覆盖完整内容。
4. 不要一次写入过多无关文件，按最小必要顺序创建。
5. 同一轮中先创建配置文件，再创建入口文件，再创建页面和组件文件。

禁止事项：
1. 不要直接在普通文本中输出完整文件代码。
2. 不要输出技术说明、实现总结、部署教程。
3. 不要输出“下面是代码”“以下是实现”之类的冗余前言。
4. 不要使用 history 路由。
5. 不要使用以服务器绝对路径为基础的写文件路径。

输出约束：
1. 首轮尽量控制在 30 个文件以内。
2. 总内容尽量控制在合理规模，先保证可运行，再考虑扩展。
3. 如果用户需求很大，优先先搭建完整骨架，再补充页面细节。

你在执行时的顺序应当是：
1. 先理解用户需求。
2. 用 1 到 3 句简短文字说明准备生成什么项目。
3. 按顺序调用 writeFile 工具创建项目文件。
4. 完成后只给出非常简短的收尾说明，不要重复解释代码。

在调用工具之前，请始终记住：你的第一目标不是写很多代码，而是生成一个结构正确、配置正确、可以 build 成功的 Vue 工程。
```

## 7.1 推荐的补充上下文提示

如果后续采用“预置模板 + AI 修改”的增强方案，可以在用户消息前拼接一段结构化上下文，告诉模型当前有哪些文件已经存在。建议格式如下：

```json
[
  {
    "filePath": "package.json",
    "desc": "项目依赖配置",
    "content": "文件完整内容"
  },
  {
    "filePath": "src/main.js",
    "desc": "应用入口文件",
    "content": "文件完整内容"
  }
]
```

这段上下文不是第七阶段必做项，但它对提升生成稳定性非常有效，尤其适合“先复制一个极简 Vue 模板，再让 AI 在模板上迭代”的策略。

## 7.2 提示词中的硬性配置片段

无论最终版本号采用哪一组，提示词都应该明确要求 AI 生成如下关键配置。

`vite.config.js` 关键要求：

```js
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
```

`src/router/index.js` 关键要求：

```js
import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [],
})

export default router
```

`package.json` 至少要有：

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

## 8. 流式消息协议设计

## 8.1 为什么要统一协议

如果继续沿用当前仓库的纯文本流式输出，前端只能看到一段段普通字符串，无法分辨：

- 哪些是 AI 正在解释自己的意图。
- 哪些是工具调用请求。
- 哪些是工具执行完成并已经真正写入文件。

这会直接影响两个地方：

- 前端实时体验差。
- 数据库存储的聊天记录会变成一团无法阅读的原始文本或原始 JSON。

所以第七阶段必须引入统一流式消息协议。

## 8.2 消息类型

建议定义下面 3 类消息：

- `ai_response`：AI 自然语言回复。
- `tool_request`：AI 发起工具调用请求。
- `tool_executed`：工具执行完成。

对应消息类建议如下：

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

枚举类建议固定为：

```java
AI_RESPONSE("ai_response", "AI响应")
TOOL_REQUEST("tool_request", "工具请求")
TOOL_EXECUTED("tool_executed", "工具执行结果")
```

注意：这些消息类必须带无参构造函数，否则 JSON 反序列化会失败。

## 8.3 流消息示例

原始 TokenStream 事件大致可能是这样的：

```text
AI 回复：为你生成一个 Vue 项目
工具调用请求：writeFile(index.html, ...)
工具调用请求：writeFile(src/main.js, ...)
工具执行完成：writeFile(index.html)
工具执行完成：writeFile(src/main.js)
AI 回复：生成完成
```

统一封装后，应当变成：

```json
{"type":"ai_response","data":"为你生成一个 Vue 项目"}
{"type":"tool_request","id":"call_0","name":"writeFile","arguments":"{...}"}
{"type":"tool_executed","id":"call_0","name":"writeFile","arguments":"{...}","result":"文件写入成功：index.html"}
{"type":"ai_response","data":"生成完成"}
```

## 8.4 与现有 SSE 包装的兼容关系

当前 `AppController#chatToGenCode()` 会把每个 chunk 再包装成：

```json
{"d":"chunk内容"}
```

所以第七阶段需要注意一个事实：

- 外层 SSE 结构可以先不改，继续保持现有接口兼容。
- 但 `vue_project` 模式下，`d` 字段内部不再是纯文本，而是 `StreamMessage` 的 JSON 字符串。

也就是说前端处理时要做两层解析：

1. 先解析 SSE 的外层 `{"d":"..."}`。
2. 再判断 `d` 是否是 `StreamMessage` JSON。

这样做的好处是：

- 不破坏老模式。
- 新模式可以逐步接入。

## 9. 文件写入工具设计

## 9.1 工具接口

建议的工具接口签名：

```java
@Tool("写入文件到指定路径")
public String writeFile(
    @P("文件的相对路径") String relativeFilePath,
    @P("要写入文件中的完整内容") String content,
    @ToolMemoryId Long appId
)
```

这里的 `@ToolMemoryId` 很关键。没有它，工具层无法知道当前应该把文件写到哪个应用目录。

## 9.2 工具实现约束

工具实现必须满足：

- 只接受相对路径。
- 自动把相对路径映射到 `temp/code_output/vue_project_{appId}` 下。
- 自动创建父目录。
- 写文件时使用覆盖写入，而不是追加写入。
- 返回值只包含相对路径，不包含绝对路径。

推荐实现逻辑：

```java
Path path = Paths.get(relativeFilePath);
if (!path.isAbsolute()) {
    String projectDirName = "vue_project_" + appId;
    Path projectRoot = Paths.get(AppConstant.CODE_OUTPUT_ROOT_DIR, projectDirName);
    path = projectRoot.resolve(relativeFilePath);
}
```

然后：

- `Files.createDirectories(parentDir)`
- `Files.write(path, content.getBytes(), CREATE, TRUNCATE_EXISTING)`
- 返回 `文件写入成功：` + `relativeFilePath`

## 9.3 安全注意事项

这个工具最容易踩 4 个坑：

- 路径穿越：必须拒绝 `..` 越界写入。
- 绝对路径泄露：不能把真实服务器路径回传给模型或用户。
- 反复覆盖错误文件：必须用 `appId` 绑定目录，防止串应用写入。
- 编码问题：统一 UTF-8。

## 10. Chat Memory 与 Service 工厂改造

## 10.1 为什么必须改造工厂

当前 `AiCodeGenServiceFactory` 是一个简单的全局 Bean 工厂：

- 注入一个 `chatModel`
- 注入一个 `streamingChatLanguageModel`
- 构建一个 `AiCodeGeneratorService`

这个实现对 `single_file` / `multi-file` 够用，但对 `vue_project` 不够，原因是：

- 不同 `appId` 的对话上下文不能混。
- 不同 `codeGenType` 不能共用一套 Service。
- `vue_project` 需要工具和记忆，老模式不需要。

## 10.2 工厂重构后的策略

重构后的工厂应当满足：

- 根据 `appId + codeGenType` 生成缓存 key。
- 对 `vue_project` 返回带工具、带记忆、带推理模型的 Service。
- 对旧模式继续返回普通 Service。

推荐缓存键策略：

```java
private String buildCacheKey(long appId, CodeGenTypeEnum codeGenType) {
    return appId + ":" + codeGenType.getValue();
}
```

## 10.3 为什么建议引入 Caffeine

如果每一次对话都现场构建一个新的 AI Service，会有两个问题：

- 重复初始化对象，浪费资源。
- 同一应用连续多次操作时，服务实例频繁重建，不利于调试。

所以建议工厂层加一层 Caffeine 缓存，按 `appId + codeGenType` 缓存服务实例，并配置合理过期时间，比如：

- `maximumSize(1000)`
- `expireAfterWrite(30 minutes)`
- `expireAfterAccess(10 minutes)`

## 10.4 记忆加载策略

建议不要把“从数据库读取历史并转成 ChatMemory”写在 `AppServiceImpl` 里，否则职责会越堆越重。推荐抽一个独立组件，例如：

- `core/memory/ChatMemoryLoader.java`

它负责：

- 查询最近 N 条聊天记录。
- 按 `messageType` 转成 UserMessage / AiMessage。
- 加载进 `MessageWindowChatMemory`。

这样工厂只负责组装，不负责取数细节。

## 11. Facade 与流适配改造

## 11.1 为什么不能复用老的 executeSaverStream

当前 `CodeFileSaverExecutor.executeSaverStream()` 的逻辑是：

- 收集整段文本。
- 流结束后解析。
- 再一次性保存文件。

这对 `vue_project` 完全不合适，因为 `vue_project` 是边生成边写文件。第七阶段必须明确分流：

- `single_file` / `multi-file`：继续走老链路。
- `vue_project`：直接走 TokenStream 适配链路，不再做整段解析保存。

## 11.2 Facade 的建议行为

`AiCodeGeneratorFacade#generateAndSaveCodeStream()` 建议改造成：

- `SINGLE_FILE` -> 旧逻辑。
- `MULTI_FILE` -> 旧逻辑。
- `VUE_PROJECT` -> `generateVueProjectCodeStream(appId, userMessage)`，然后进入 `processTokenStream(...)`。

这一步要写得很清楚，不要为了“统一看起来更优雅”而强行把三种模式揉成同一套处理逻辑。

## 12. LangChain4j 工具流式输出方案

## 12.1 现实问题

图片里已经把这个问题说明白了：真正难的不是“调用工具”，而是“在流式过程中把工具调用过程实时展示出来”。

理想状态下，我们希望拿到：

- 工具调用的部分参数流。
- 工具调用完成事件。
- AI 文本回复。

但不同版本的 LangChain4j 对这些回调的支持并不一致，而且新版本虽然开始支持部分能力，也可能存在兼容性问题。

## 12.2 第七阶段建议采用的策略

第七阶段建议分成“当前可落地方案”和“未来升级方案”两层。

### 当前可落地方案

- 允许复制 LangChain4j 中和 TokenStream 回调有关的最小必要源码到项目内。
- 给 TokenStream 增加工具请求流式回调和工具执行完成回调。
- 通过这层临时增强，稳定拿到工具流消息。

这是一个明确的“工程折中”，不是最优雅的方案，但它能最快把功能做出来。

### 未来升级方案

- 后续跟进 LangChain4j 新版本的官方支持。
- 等官方对 `PartialToolCall`、`CompleteToolCall`、`PartialThinking` 的支持稳定后，再移除项目内覆盖源码。

## 12.3 为什么现在不完全依赖官方新接口

即使 LangChain4j 新版本开始支持更多流式事件，第七阶段也不建议立刻把整个方案绑定到官方新接口上，原因是：

- 部分事件在工具参数为空字符串时可能触发异常。
- 新接口可用，不等于在当前项目环境里稳定可用。
- 当前阶段优先级是“把链路跑通”，不是“把第三方库用得最优雅”。

## 13. 流处理器设计

## 13.1 SimpleTextStreamHandler

职责：只处理老模式纯文本流。

行为：

- 原样向前端输出文本块。
- 在流结束时拼接成完整 AI 消息写入聊天记录。
- 如果异常，记录失败消息。

这个类本质上就是把现在散落在 `AppServiceImpl` 里的老逻辑提炼出来，目的不是炫技，而是给 `vue_project` 模式腾出独立处理空间。

## 13.2 JsonMessageStreamHandler

职责：处理 `vue_project` 模式的 JSON 流消息。

它需要做 3 件事：

- 解析 JSON 消息类型。
- 把消息转换成前端可展示的文本片段。
- 把消息转换成数据库可读的会话文本。

建议规则如下：

- `ai_response`：直接把 `data` 追加到前端显示与历史文本。
- `tool_request`：同一个工具调用 ID 只在第一次出现时向前端输出“正在写入某文件”的提示。
- `tool_executed`：把最终写入的 `relativeFilePath`、文件后缀、内容摘要整理成结构化展示文本。

推荐的展示格式：

```text
[工具调用] 写入文件 src/router/index.js
```

或者：

````text
[工具调用] 写入文件 src/router/index.js
```js
// 文件内容摘要
```
````

是否把完整文件内容推给前端，要由产品体验决定。第七阶段建议优先显示文件路径和少量摘要，不要把整份文件内容反复打到会话流里，避免消息量爆炸。

## 13.3 StreamHandlerExecutor

这个执行器的职责非常单纯：根据 `CodeGenTypeEnum` 路由到不同处理器。

推荐规则：

- `SINGLE_FILE` -> `SimpleTextStreamHandler`
- `MULTI_FILE` -> `SimpleTextStreamHandler`
- `VUE_PROJECT` -> `JsonMessageStreamHandler`

不要在 `AppServiceImpl` 里写一堆 `if-else` 直接处理所有细节。让执行器做模式分发，服务层只负责业务编排。

## 14. Vue 工程构建、预览、部署

## 14.1 为什么必须有固定构建流程

AI 负责生成文件，但不能让 AI 决定“要不要构建”“用什么命令构建”“要不要部署”。这些都必须是服务端的固定流程。

第七阶段固定流程建议如下：

1. 生成完成。
2. 运行 `npm install`。
3. 运行 `npm run build`。
4. 检查 `dist` 是否存在。
5. 预览读取 `dist/index.html`。
6. 部署复制 `dist` 到部署目录。

## 14.2 构建服务建议

建议新增 `VueProjectBuildService`，封装以下职责：

- 根据 `appId` 找到工程目录。
- 执行 `npm install`。
- 执行 `npm run build`。
- 收集 stdout / stderr。
- 超时控制。
- 构建失败时报错并保留日志。

实现细节建议：

- 使用 `ProcessBuilder`。
- 设置 working directory 为 `temp/code_output/vue_project_{appId}`。
- Windows 下使用 `npm.cmd`，Unix 下使用 `npm`。
- `npm install` 和 `npm run build` 分开执行，分别检查退出码。
- 输出日志写到内存字符串或单独日志文件，失败时返回摘要，完整日志写服务端日志。

## 14.3 预览路径

由于 `WebMvcConfig` 已经把 `temp/code_output` 映射到 `/static/**`，所以 `vue_project` 预览路径建议固定为：

```text
/api/static/vue_project_{appId}/dist/index.html
```

要求 `vite.config.js` 的 `base` 必须是 `./`，否则静态资源在子路径下会加载失败。

## 14.4 部署逻辑改造

当前 `AppServiceImpl#deployApp()` 直接复制 `code_output/{codeGenType}_{appId}` 目录。对于 Vue 工程，这个目录是源码目录，不是可部署目录。

第七阶段建议改成：

- 如果 `codeGenType != vue_project`，沿用旧逻辑。
- 如果 `codeGenType == vue_project`：
  - 先检查 `dist` 是否存在。
  - 如果不存在，自动触发构建。
  - 构建成功后，复制 `dist` 到 `temp/code_deploy/{deployKey}`。

这样部署 URL 仍然可以沿用：

```text
http://localhost/{deployKey}/
```

## 15. 开发注意事项与风险清单

## 15.1 模型可能反复调用同一个工具

表现：

- 同一个文件被重复写多次。
- 工具调用循环。

应对：

- 扩大记忆窗口。
- 优化系统提示词。
- 必要时在工具层增加简单保护，比如对相同内容重复写入直接短路。

## 15.2 工具参数可能是流式碎片

表现：

- 一个完整的 `relativeFilePath` 或 `content` 被拆成很多块。

应对：

- `tool_request` 只做“展示用途”，不要在这个阶段解析出最终文件。
- 真正可信的数据以 `tool_executed` 为准。

## 15.3 不要把绝对路径泄露出去

这条非常重要。工具返回值里只能出现：

- `src/App.vue`
- `package.json`
- `vite.config.js`

不能出现：

- `E:/Programme/Project/...`
- `C:/Users/...`

否则用户可以看到服务端真实目录结构，属于明显信息泄露。

## 15.4 不要把原始 JSON 流直接存到聊天记录

如果直接把：

```json
{"type":"tool_request","id":"call_1"...}
```

这种内容存进 `chat_history.message`，历史对话会非常难看，也不利于后续给模型回放上下文。数据库里应该存“已经整理过的用户可读文本”。

## 15.5 `AppAddRequest` 不要继续硬编码模式

当前 `AppController#addApp()` 里把 `codeGenType` 硬编码成 `multi-file`，这是第七阶段必须改掉的点。

推荐做法：

- 给 `AppAddRequest` 增加 `codeGenType` 字段。
- 后端校验只允许枚举值。
- 第七阶段前端默认传 `vue_project`。

这比继续在控制层写死模式要干净得多。

## 15.6 构建不是 AI 的责任

不要给模型 `npm install`、`npm run build`、`deploy` 这类工具。第七阶段这些步骤必须是程序固定流程。原因：

- AI 不擅长管理长耗时构建命令。
- 构建失败的重试策略应该由后端控制。
- 构建与部署属于平台基础设施，不属于模型决策范围。

## 16. 实施任务拆分

下面的任务拆分按推荐执行顺序排列。这里不展开业务页面代码，只展开第七阶段基础设施改造。

### Task 1：升级依赖与补齐配置基线

**Files:**

- Modify: `pom.xml`
- Modify: `src/main/resources/application.yml`

**目标：**

- 升级 LangChain4j 相关依赖到统一版本线。
- 引入 Caffeine。
- 引入 Redis 依赖或等价记忆存储依赖。
- 增加 `app.ai.vue-project.*` 配置。

**关键决策：**

- `vue_project` 专用模型配置独立出来。
- 不在该模型上强绑 JSON response-format。

**验证：**

- `mvn test -Dtest=AiCodeGeneratorFacadeTest`
- 应用能正常启动，不出现 Bean 冲突。

### Task 2：扩展枚举、请求 DTO、Prompt 资源

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/model/enums/CodeGenTypeEnum.java`
- Modify: `src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java`
- Modify: `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- Create: `src/main/resources/prompt/codegen-vue-project-system-prompt.txt`

**目标：**

- 新增 `VUE_PROJECT("Vue 工程模式", "vue_project")`。
- `AppAddRequest` 支持传 `codeGenType`。
- 创建应用时不再硬编码 `multi-file`。
- 新增系统提示词资源文件。

**关键决策：**

- 老数据不迁移，新增数据直接使用新枚举。
- 默认值由前端决定，不再由后端控制层硬编码。

**验证：**

- 新建应用接口能创建 `codeGenType=vue_project` 的记录。

### Task 3：新增推理模型配置与文件写入工具

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/config/ReasoningStreamingChatModelConfig.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`
- Modify: `src/main/java/com/adcage/acaicodefree/constant/AppConstant.java`

**目标：**

- 创建独立的 `reasoningStreamingChatModel` Bean。
- 实现 `writeFile(relativeFilePath, content, appId)` 工具。
- 固定 `vue_project_{appId}` 目录约定。

**关键决策：**

- 工具只接受相对路径。
- 返回值只返回相对路径。
- 目录命名使用 `vue_project_{appId}`，不再沿用老的 `codeGenType + '_' + appId` 纯字符串推断方式。

**验证：**

- 单元测试验证工具可创建目录、可写文件、不可越界写入。

### Task 4：重构 AI Service 工厂与记忆加载

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
- Create: `src/main/java/com/adcage/acaicodefree/core/memory/ChatMemoryLoader.java`

**目标：**

- 新增 `generateVueProjectCodeStream(@MemoryId long appId, String userMessage)`。
- 工厂按 `appId + codeGenType` 创建服务。
- `vue_project` 模式挂载 `FileWriteTool`、ChatMemory、推理模型。
- 老模式继续沿用普通模型。

**关键决策：**

- `vue_project` 模式必须有记忆。
- 服务实例必须缓存。
- 记忆加载逻辑从业务服务抽离。

**验证：**

- 连续两轮生成时，模型能够感知已经写过的文件。

### Task 5：新增流消息模型与 TokenStream 适配层

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/AiResponseMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolRequestMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/ToolExecutedMessage.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/model/message/StreamMessageTypeEnum.java`
- Modify: `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`

**目标：**

- 把 TokenStream 事件统一转成 `Flux<String>` JSON 消息流。
- 为后续前端展示和后端落库提供统一数据格式。

**关键决策：**

- `vue_project` 模式的流不再是纯文本。
- 统一协议优先于临时字符串拼接。

**验证：**

- 给定一组模拟 TokenStream 事件，能输出正确的 JSON 消息串。

### Task 6：实现流处理器并改造聊天记录落库

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/core/handler/SimpleTextStreamHandler.java`
- Create: `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`
- Create: `src/main/java/com/adcage/acaicodefree/core/handler/StreamHandlerExecutor.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

**目标：**

- 老模式继续按纯文本处理。
- `vue_project` 模式按 JSON 消息处理。
- 数据库存储不再是原始 JSON，而是整理后的可读文本。

**关键决策：**

- 同一 `tool_request` ID 只提示一次。
- 最终可信写文件信息以 `tool_executed` 为准。

**验证：**

- 历史消息页面看到的是人类可读内容，不是 JSON 原文。

### Task 7：引入构建服务并打通预览 / 部署

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/core/build/VueProjectBuildService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- Modify: `src/main/java/com/adcage/acaicodefree/config/WebMvcConfig.java`（如果需要补充路径说明）

**目标：**

- 生成完成后固定执行 `npm install`、`npm run build`。
- 预览路径切到 `dist/index.html`。
- 部署复制 `dist` 而不是源码目录。

**关键决策：**

- 构建流程由后端固定执行，不让 AI 调用命令工具。
- 若 `dist` 不存在，部署前自动触发构建。

**验证：**

- 生成一个最小 Vue 项目后，能在 `temp/code_output/vue_project_{appId}/dist` 看到产物。

### Task 8：兼容 SSE 输出与前端解析契约

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- Modify: `docs/learn/AI-CodeGen-Frontend-Implementation.md`（如需补充前端解析说明）

**目标：**

- 保持现有 SSE 外层 envelope 不变。
- 明确 `vue_project` 模式下 `d` 字段是二层 JSON。
- 增加文档说明前端如何解析新协议。

**关键决策：**

- 先兼容，不激进改接口。

**验证：**

- 老模式仍能正常显示。
- 新模式能显示 AI 回复与工具进度。

### Task 9：补齐单元测试与集成验证

**Files:**

- Modify: `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeTest.java`
- Create: `src/test/java/.../FileWriteToolTest.java`
- Create: `src/test/java/.../JsonMessageStreamHandlerTest.java`
- Create: `src/test/java/.../VueProjectBuildServiceTest.java`

**目标：**

- 覆盖工具写文件安全性。
- 覆盖 JSON 消息处理逻辑。
- 覆盖构建服务命令执行逻辑。
- 保留一个手工可运行的真实模型集成测试。

**关键决策：**

- 大部分测试不依赖真实模型。
- 真实模型测试作为本地集成测试，不作为常规 CI 强依赖。

**验证：**

- `mvn test`
- 本地带真实 API Key 时，`generateVueProjectCodeStream()` 能落地最小工程。

## 17. 验收标准

第七阶段完成后，至少要满足下面这些验收项：

- 可以新建 `codeGenType=vue_project` 的应用。
- AI 能通过工具逐文件生成 Vue 工程。
- 前端能实时看到 AI 回复和工具调用进度。
- 工具返回信息不泄露绝对路径。
- 同一应用多轮生成不会明显重复忘记之前写过的文件。
- 生成完成后会自动构建，并产出 `dist`。
- 预览地址可以直接访问 `dist/index.html`。
- 部署时复制的是 `dist` 目录。
- 聊天记录保存的是可读文本，而不是原始 JSON 流。
- 老的 `single_file` / `multi-file` 模式不被破坏。

## 18. 可选增强项（不计入第七阶段必须交付）

这些内容和图片里也有关联，但不建议挤进第七阶段主任务里：

- 预置 Vue 模板后再让 AI 在模板上改写。
- 深度思考消息单独流式展示。
- 构建日志可视化。
- 失败后的断点恢复和重试。
- 允许 AI 修改而不是新建某些白名单文件。

这些都值得做，但要建立在第七阶段主链路已经稳定的前提下。

## 19. 最后结论

如果只用一句话概括第七阶段，那就是：

**从“让模型吐代码文本”升级到“让模型像工程助手一样写项目文件，并把整个过程真实、可读、可构建地展示出来”。**

这一步的关键不是页面好不好看，而是下面这条基础设施链路是否真正打通：

- 模式切换
- 模型配置
- 工具调用
- 记忆绑定
- 流式协议
- 聊天落库
- 自动构建
- 预览部署

第七阶段把这条链路跑通，后面的 Agent 化、多模板、多框架支持、深度思考展示，才有继续往上叠的价值。
