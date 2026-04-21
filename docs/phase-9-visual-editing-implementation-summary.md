# 第九阶段：可视化修改与局部编辑能力 实施总结

## 1. 文档目的

本文档用于详细记录第九阶段“可视化修改与局部编辑能力”的实际落地情况。内容不只说明“改了哪些文件”，还会明确解释以下几点：

1. 每个文件在这一阶段承担了什么职责。
2. 代码相对改造前的差异是什么。
3. 为什么要这样改，而不是沿用旧实现。
4. 这些代码改动最终给前端交互、后端 AI 修改链路、工具展示能力和测试回归带来了什么效果。

这一阶段的核心目标不是把平台改造成低代码编辑器，而是在现有“对话生成 / 对话修改”的基础上，补齐“用户在预览页直接点选目标元素，再让 AI 精准修改该区域”的完整闭环。

---

## 2. 本阶段最终交付了什么

第九阶段最终完成的能力，不是单点功能，而是一条从前端选择、到提示词增强、到后端差异化执行、到工具结果展示、再到测试验证的完整链路。具体来说，平台现在已经具备以下能力：

- 用户可以在应用预览区进入编辑模式。
- 编辑模式下，iframe 内页面会被动态注入选区脚本，而不是把平台编辑代码固化进用户生成的网站源码。
- 用户悬浮页面元素时，目标节点会出现 hover 高亮；点击后，会进入 selected 高亮状态。
- 前端会采集被选中元素的结构化信息，包括标签名、id、class、文本摘要、层级 selector、页面路径和位置信息。
- 用户发送新消息时，系统会自动把“选中元素信息”和“修改需求”拼成增强提示词发给后端，从而把“改这里”变成机器可理解的上下文。
- 后端原生模式（`SINGLE_FILE` / `MULTI_FILE`）通过更严格的 prompt 约束，减少无关区域误改。
- 后端 Vue 工程模式（`VUE_PROJECT`）从原先只支持写文件，扩展为读目录、读文件、改文件、写文件、删文件的一整套增量工具链。
- 工具调用不再只是粗糙地显示“成功 / 失败”，而是可以向前端消息区输出“准备修改哪个文件”“已经读取哪个目录”“已完成哪项替换”等更可读的过程信息。
- 创建场景与修改场景在服务接口和 prompt 层面完成分流，避免“本来只想改标题，模型却按新建页面思路整体重写”的问题。
- 已补齐对应的单元测试、后端端到端测试和前后端链路端到端测试，并在全部代码完成后统一执行通过。

---

## 3. 本阶段的整体实现结构

本阶段最终落地的整体结构可以概括为 4 层：

### 3.1 前端交互层

由 `AppGeneratorPage.vue` 和 `visualEditor.ts` 组成。

- `AppGeneratorPage.vue` 负责页面上的业务 UI，包括编辑模式按钮、选中元素信息展示区、聊天输入框、SSE 消息展示、预览 iframe 生命周期联动。
- `visualEditor.ts` 负责把“预览 iframe”变成一个可选择元素的轻量编辑容器，包括脚本注入、事件监听、高亮样式、消息通信、选区清理等。

### 3.2 提示词组装层

前端在发送消息前，不再直接把用户原始文本送到后端，而是在存在选区时，把消息重组成如下自然语言结构：

- 选中元素信息
- 页面路径
- 标签
- 选择器
- 当前内容
- 修改需求

这样做的价值在于：后端和模型不必解析一段结构化 JSON，而是直接获得对提示词更友好的自然语言上下文。

### 3.3 后端执行分流层

`AiCodeGeneratorFacade` 在这一阶段的关键职责，是根据用户消息是否属于“可视化修改请求”来自动分流：

- 普通创建请求：走原有生成链路。
- 可视化修改请求：走修改专用 prompt / 修改专用流式接口。

这一步解决了一个很关键的问题：同样是“发一句话给 AI”，创建页面和修改页面在约束上完全不同，如果仍共用一套生成思路，模型会天然偏向重建而不是局部修补。

### 3.4 Vue 工程工具化层

对于 `VUE_PROJECT`，本阶段实现的重点不是“更聪明的 prompt”，而是“可执行的增量工具系统”：

- `readDir` 用于让模型先建立目录结构认知。
- `readFile` 用于读取已有文件内容。
- `modifyFile` 用于在命中旧内容时做字符串替换。
- `writeFile` 用于创建新文件或覆盖式写入。
- `deleteFile` 用于删除普通文件，同时保护关键骨架文件不被误删。

工具层不是孤立存在的，而是配套统一的展示接口和管理器，一起被注入到 LangChain4j 的 AI service 中。

---

## 4. 前端改动详解

## 4.1 `ac-ai-code-free-fronted/vite.config.ts`

### 改动内容

在 Vite 配置中新增了本地开发代理：

```ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8700',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

### 改造前的问题

改造前，前端运行在 `5173`，后端和静态预览资源运行在 `8700`，属于不同端口，浏览器会视为不同源。这样父页面不能稳定访问 iframe DOM，也无法向 iframe 内部动态注入编辑脚本。

### 改造后的作用

通过把 API 和静态资源入口都收敛到 `/api` 代理，本地开发时前端可以经由同一个来源访问预览内容，为 iframe 注入脚本提供技术前提。这不是“体验优化”，而是本阶段编辑模式能够真正落地的基础条件。

---

## 4.2 `ac-ai-code-free-fronted/.env.development`

### 改动内容

本地环境变量由绝对地址改为相对路径：

- `VITE_API_BASE_URL=/api`
- `VITE_APP_DEPLOY_URL_PREFIX=/api/static`

保留：

- `VITE_APP_DEPLOY_HOST=http://localhost`

### 改造前的问题

之前配置里 API 和静态预览地址都是 `http://localhost:8700/...` 的绝对路径，虽然请求本身能通，但在父页面和 iframe 的同源策略下不利于编辑模式工作。

### 改造后的作用

改成相对路径后，前端所有访问都通过当前站点发起，再由 Vite 代理转发到后端。这样 `AppGeneratorPage` 中的 iframe 预览地址和接口访问路径都对齐到同一个来源模型，避免编辑模式被浏览器同源策略直接拦住。

---

## 4.3 `ac-ai-code-free-fronted/src/utils/visualEditor.ts`

这是第九阶段前端新增的核心文件，也是“可视化编辑”能力真正成立的基础。

### 新增内容一：元素信息结构 `ElementInfo`

这个类型定义了前端在用户点击元素后向主页面传递的数据结构：

- `tagName`
- `id`
- `className`
- `textContent`
- `selector`
- `pagePath`
- `rect`

相比只传一个 DOM 引用或者只传文本内容，这个结构明显更完整，因为它同时兼顾了：

- AI 定位所需的语义信息
- 页面路径上下文
- 在 UI 展示中可直接输出的内容
- 后续扩展（例如更精细的选择器策略、坐标辅助）

### 新增内容二：动态注入脚本 `buildInjectedScript`

这一部分不是在业务页面里直接写 `<script>` 标签，而是由主页面在 iframe 加载完成后，临时向 `contentDocument` 注入一段脚本。

脚本内部完成了以下事情：

1. 建立全局状态对象，记录是否开启编辑模式、当前 hover 元素、当前 selected 元素和提示条节点。
2. 定义跳过节点集合，忽略 `html`、`head`、`body`、`script`、`style` 等不适合作为业务修改目标的节点。
3. 生成可读 selector：不是追求浏览器级绝对精确复现，而是给 AI 提供足够的层级上下文。
4. 采集元素信息：把文本归一化、裁剪到 120 字符，避免把过长整段正文直接塞进提示词。
5. 插入 hover / selected 高亮样式。
6. 在右上角插入“编辑模式已开启：悬浮查看，点击选中元素”的提示条，帮助用户理解当前交互状态。

### 新增内容三：事件拦截逻辑

脚本使用捕获阶段监听：

- `mouseover`
- `mouseout`
- `click`
- `message`

其中最关键的是 click 拦截逻辑：

```ts
event.preventDefault()
event.stopPropagation()
event.stopImmediatePropagation()
```

它的目的不是“让页面不能点”，而是保证编辑模式下点击按钮、链接、卡片时，不会触发原页面导航或交互行为，从而把点击行为稳定地解释为“选择这个元素”。

### 新增内容四：主页面控制器 `createVisualEditor`

`createVisualEditor` 把 iframe 编辑能力封装成一个前端工具对象，暴露的方法包括：

- `enterEditMode()`
- `exitEditMode()`
- `clearSelection()`
- `handleIframeLoad()`
- `dispose()`

这样做的好处是把复杂的注入和通信逻辑从页面组件中抽离出去，避免 `AppGeneratorPage.vue` 出现大量难以维护的脚本拼接代码。页面组件只负责在合适的时机调用这些方法，而不用知道内部注入细节。

---

## 4.4 `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`

这是第九阶段前端改动量最大的文件，因为它是聊天页、预览页和编辑页三种交互的汇合点。

### 改动内容一：新增编辑模式入口 UI

在预览区顶部操作栏中新增了：

- “进入编辑模式 / 退出编辑模式”按钮
- “清除选中”按钮

这两个按钮与已有的“桌面端 / 移动端切换”“刷新预览”放在同一个区域，形成统一的预览操作条。

相比改造前只有刷新按钮，现在用户能明确知道：预览区不只是看结果，还可以进入“点选修改”的模式。

### 改动内容二：新增选中元素信息区

在聊天消息区与输入框之间插入了一个 `a-alert` 信息卡片，用来展示：

- 标签
- 页面路径
- selector
- 文本摘要

这个区域非常关键，因为它承担了两个作用：

1. 告诉用户“当前系统理解的目标元素是谁”，防止误选。
2. 为后续输入提供心理暗示，让用户自然以“修改这个元素”为上下文去继续对话。

如果没有这一层，用户实际上不知道平台到底选中了什么，只能凭高亮猜测，交互信心会明显下降。

### 改动内容三：输入框 placeholder 动态变化

新增了 `inputPlaceholder` 计算属性：

- 未选中元素时：`描述具体的需求，例如：修改配色为深色模式...`
- 已选中元素时：`已选择页面元素，请描述要修改的内容...`

这一点虽然代码量不大，但实际很重要。它把“对话生成”和“局部修改”两种模式在输入体验上区分开了。用户一旦选中元素，会立刻明白自己接下来应该输入的是“修改这个元素的需求”，而不是重新描述整站需求。

### 改动内容四：接入 `visualEditor`

页面通过 `createVisualEditor` 创建编辑器实例，并把 `iframeRef` 交给它：

- `onElementSelected` 负责把 iframe 回传的元素信息同步到 `selectedElement`
- `onModeChange` 负责驱动 `editMode` 状态
- `handleIframeLoad` 在 iframe 刷新或重新加载后重新挂回编辑模式

这里的关键点在于：编辑器实例不持有业务状态，页面只把“选中了哪个元素”“当前是否编辑模式”作为响应式状态管理。这样不会让工具层侵入业务逻辑。

### 改动内容五：发送消息前自动拼接可视化上下文

本阶段在页面中新增了 `buildSelectedElementPrompt`。它的作用是：

- 如果当前没有选中元素，保持原有消息发送逻辑。
- 如果当前已选中元素，则把用户原始输入包装成：

```text
选中元素信息：
- 页面路径：...
- 标签：...
- 选择器：...
- 当前内容：...

修改需求：...
```

注意这里的一个实现细节：

- 页面消息列表中展示给用户的，仍然是用户原始输入。
- 真正发送到 SSE 接口里的，则是增强后的 prompt。

这样做比“直接在 UI 里显示一大段拼装后的上下文”更合理，因为它兼顾了后端精度和前端可读性。

### 改动内容六：Vue 工程工具消息展示增强

此前 `appendVueProjectChunk` 的逻辑几乎只会展示写文件相关文案，例如“准备写入文件”“已写入文件”。这对于新增的读目录、读文件、改文件、删文件工具明显不够。

因此这一阶段新增了 `formatToolText`，按工具名把不同工具映射成更贴近用户理解的文本，例如：

- `writeFile` -> 准备写入文件 / 已写入文件
- `readFile` -> 准备读取文件 / 已读取文件
- `modifyFile` -> 准备修改文件 / 已修改文件
- `deleteFile` -> 准备删除文件 / 已删除文件
- `readDir` -> 准备读取目录 / 目录结构读取完成

这意味着前端消息区已经不再默认把所有工具当成写文件流程，而是能真实反映增量修改过程。

### 改动内容七：选区状态与预览生命周期联动

页面在以下场景中会主动清理选区：

- 刷新 iframe
- 更新预览地址
- 新建会话
- 切换会话
- 退出编辑模式
- 组件卸载

这一点解决的是“脏选区残留”问题。否则用户切换到另一个会话或刷新页面后，之前的选中元素上下文仍残留在当前状态里，后续消息就可能被错误拼接到新的请求中。

---

## 5. 后端服务与执行链路改动详解

## 5.1 `src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`

### 改动内容

在原有“生成类接口”之外，新增了修改专用的流式接口：

- `modifySingleFileCodeStream`
- `modifyMultiFileCodeStream`
- `modifyVueProjectCodeStream`

并分别绑定到新的修改 prompt：

- `codegen-single-file-modify-system-prompt.txt`
- `codegen-multi-file-modify-system-prompt.txt`
- `codegen-vue-project-modify-system-prompt.txt`

### 改造前的问题

改造前，创建场景与修改场景共用一套接口和 prompt。这样做的直接后果是：用户明明只想改一个标题，模型仍然可能按“重新设计页面”的思路返回完整新方案。

### 改造后的作用

通过接口分流，系统在服务层就表达清楚两种不同的任务语义：

- 创建：强调从零产出
- 修改：强调保守、局部、最小必要变更

这一步并不是形式上的“多加几个方法”，而是把修改场景从根上从“生成思维”里拆了出来。

---

## 5.2 `src/main/java/com/adcage/acaicodefree/core/VisualEditPromptHelper.java`

### 改动内容

新增一个非常轻量的辅助类，通过判断用户消息中是否同时包含：

- `选中元素信息：`
- `修改需求：`

来识别这是否是可视化修改请求。

### 为什么需要这个类

如果把这段判断逻辑散落在 `AiCodeGeneratorFacade` 或更深层的工具注入逻辑里，后续会越来越难维护。单独抽出一个 helper 有两个好处：

1. 让“什么叫可视化修改请求”成为一个明确、可测试的规则。
2. 为单元测试提供稳定入口，不需要每次都走完整 AI 调用链才能验证分流逻辑。

---

## 5.3 `src/main/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java`

这是本阶段后端执行链路中的枢纽文件。

### 改动内容一：根据消息内容自动识别修改请求

在 `generateAndSaveCodeStream` 中新增：

```java
boolean modifyRequest = VisualEditPromptHelper.isVisualEditRequest(userMessage);
```

随后根据 `codeGenType` 和 `modifyRequest` 的组合，决定具体调用哪条 AI service 接口。

### 改动内容二：原生模式生成 / 修改分流

对于 `SINGLE_FILE` 和 `MULTI_FILE`，现在不再一律走原始生成流，而是：

- 普通请求 -> `generateSingleFileCodeStream` / `generateMultiFileCodeStream`
- 可视化修改请求 -> `modifySingleFileCodeStream` / `modifyMultiFileCodeStream`

这一步的实际效果是：原生模式虽然仍然使用“完整文件返回”机制，但模型收到的系统约束已经是“局部修改型”而不是“从零生成型”。

### 改动内容三：Vue 工程生成 / 修改分流

`buildVueProjectMessageStream` 新增 `modifyRequest` 参数：

- 若是修改请求，调用 `modifyVueProjectCodeStream`
- 否则调用 `generateVueProjectCodeStream`

这意味着 Vue 工程模式不再只是“总是按工程创建思路工作”，而是能够根据前端选区上下文切换到真正的增量修改 prompt。

### 改动内容四：工具事件继续封装为统一 JSON 流消息

这一阶段没有推翻原有 `AiResponseMessage / ToolRequestMessage / ToolExecutedMessage` 的包装结构，而是在这个结构基础上继续扩展修改场景。

这样做的价值在于：

- 前端 SSE 解析逻辑不需要完全推倒重来。
- `JsonMessageStreamHandler` 仍然可以基于统一消息格式去做工具展示和落库文案生成。

---

## 5.4 `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`

### 改动内容

把 Vue 工程模式下注入到 LangChain4j AI service 的工具，从单一的 `FileWriteTool` 改为 `ToolManager.getAllTools()` 返回的整组工具。

### 改造前的问题

此前 Vue 模式几乎只会“写文件”，缺少：

- 读目录
- 读文件
- 改文件
- 删文件

这会导致模型在修改已有工程时只能“盲写”或“覆盖写”，对真实项目几乎不可控。

### 改造后的作用

现在 AI service 在 Vue 工程模式下可以获得完整工具集。模型先理解目录结构，再读取已有文件，再选择修改方式，才真正具备“增量修改”能力，而不是靠猜路径和覆盖写文件碰运气。

---

## 6. 工具体系改动详解

## 6.1 `src/main/java/com/adcage/acaicodefree/ai/tools/BaseTool.java`

### 设计目的

这是本阶段工具体系的抽象基础类。它不是为了“炫技抽象”，而是用来解决两个实际问题：

1. 所有工具都需要共享路径安全逻辑。
2. 所有工具都需要共享“请求展示 / 结果展示”的统一接口。

### 核心能力

- `resolveProjectRoot(Long appId)`：根据应用 ID 定位 Vue 工程根目录。
- `resolveRelativePath(String relativeFilePath, Long appId)`：校验路径不能为空、不能是绝对路径、不能逃逸项目根目录。
- `extractRelativePath(JSONObject arguments)`：从工具参数中抽取 `relativeFilePath` 或 `relativeDirPath`。
- `summarizeText(String text, int maxLength)`：给 `modifyFile` 之类的工具生成简要预览文案，避免在流式展示里灌入整段长文本。
- `generateToolRequestResponse(...)` / `generateToolExecutedResult(...)`：为工具展示提供统一扩展点。

### 相比改造前的区别

之前工具没有统一抽象，路径校验和用户展示文案都只能散落在具体工具或者流处理器里。现在抽象层把安全边界和展示边界都收束到了统一位置。

---

## 6.2 `src/main/java/com/adcage/acaicodefree/ai/tools/ToolManager.java`

### 改动内容

新增一个工具注册中心，用 `BaseTool[]` 自动注入所有工具 Bean，并在 `@PostConstruct` 时建立 `toolName -> toolInstance` 的映射。

### 具体职责

- 防止重复工具名注册。
- 提供 `getTool(String toolName)` 供流处理器查找展示器。
- 提供 `getAllTools()` 供 `AiCodeGenServiceFactory` 一次性注入 LangChain4j。

### 为什么这个文件重要

如果没有 `ToolManager`，新增一个工具至少要改两处：

1. AI service 工厂里手工追加注入。
2. 流处理器里手工追加分支。

有了 `ToolManager`，新增工具的流程变成：

1. 新增工具类并继承 `BaseTool`
2. 提供工具名、展示名和展示方法
3. 让 Spring 自动收集即可

这使得工具体系从“硬编码列表”变成了“可扩展注册机制”。

---

## 6.3 `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`

### 改动内容

原来的 `FileWriteTool` 只负责写文件和简单路径校验。现在它被改造成继承 `BaseTool`，并补齐：

- `getToolName()` -> `writeFile`
- `getDisplayName()` -> `写文件`
- 请求文案生成：`准备写入文件 xxx`
- 执行完成文案生成：`已写入文件 xxx`

### 实际意义

它不再只是“能执行”的工具，同时也是“能被前端和流处理器正确展示”的工具。这样消息区看到的不再是原始工具 JSON，而是人能读懂的中文过程事件。

---

## 6.4 `src/main/java/com/adcage/acaicodefree/ai/tools/FileReadTool.java`

### 改动内容

新增读取指定文件内容的工具。

### 为什么必须新增

如果只有写文件而没有读文件，AI 对已有工程的理解只能靠猜。这在 Vue 工程修改场景里非常危险，因为：

- 可能猜错组件路径
- 可能误覆盖已有内容
- 可能在根本没读过原文件的情况下强行重写

引入 `readFile` 后，模型可以先看清楚已有实现，再决定是修改还是重写。

---

## 6.5 `src/main/java/com/adcage/acaicodefree/ai/tools/FileDirReadTool.java`

### 改动内容

新增目录结构读取工具，输出缩进式目录树字符串，而不是复杂 JSON。

### 核心实现点

- 支持空路径时读取工程根目录。
- 限制最大目录深度 `MAX_DEPTH = 6`。
- 限制单目录最大输出项数 `MAX_ENTRIES_PER_DIR = 200`。
- 使用流关闭目录句柄，避免资源泄露。

### 为什么这个工具很关键

这是本阶段 Vue 工程模式中最容易被低估、但实际上非常关键的工具。没有它，模型只能靠想象一个工程可能长什么样；有了它，模型先建立目录认知，再决定读哪些文件，整体修改命中率会高很多。

---

## 6.6 `src/main/java/com/adcage/acaicodefree/ai/tools/FileModifyTool.java`

### 改动内容

新增基于字符串替换的局部修改工具，参数为：

- `relativeFilePath`
- `oldContent`
- `newContent`

### 核心设计点

- 如果 `oldContent` 为空，直接报参数错误。
- 如果文件不存在，返回不存在错误。
- 如果原文件中找不到 `oldContent`，不强写，而是返回“未找到匹配内容”。
- 只有命中旧内容时，才执行替换和落盘。

### 为什么不是按行号改

因为 AI 在复杂上下文里给出的行号并不稳定，而“旧内容 -> 新内容”的替换语义更贴近模型能稳定表达的内容。它虽然不如 AST 级修改精确，但在当前阶段是成本更低、成功率更高的方案。

### 工具展示增强

这个工具还会把 `oldContent` / `newContent` 摘要化显示成：

`准备修改文件 xxx（替换：旧内容摘要 -> 新内容摘要）`

这比简单显示“正在修改文件”更有可读性，用户能大概知道 AI 打算替换什么。

---

## 6.7 `src/main/java/com/adcage/acaicodefree/ai/tools/FileDeleteTool.java`

### 改动内容

新增删除文件工具，但不是“任意删除”，而是带关键文件保护策略的受限删除。

### 保护范围

根目录保护文件包括：

- `package.json`
- `vite.config.js`
- `vite.config.ts`
- `vue.config.js`
- `tsconfig.json`
- `README.md`
- `.gitignore`
- 各类锁文件

项目级保护文件包括：

- `src/main.js`
- `src/main.ts`
- `src/App.vue`

### 为什么这样设计

如果让模型在 Vue 工程模式下拥有不受限制的删除能力，它很容易因为误判而删掉骨架文件，导致整个项目马上不可运行。这个工具的设计目标，不是“提供最大能力”，而是“提供可控能力”。

---

## 7. 工具消息展示链路改动详解

## 7.1 `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`

### 改造前的问题

这个处理器之前几乎只懂一件事：从工具参数里抽路径，然后拼出“准备写入文件 / 已写入文件”。它对新增工具是无感的。

也就是说，哪怕后端已经有 `readDir`、`readFile`、`modifyFile`、`deleteFile`，消息流展示依然会表现得像“只有写文件工具”。

### 改动内容

本阶段改造成：

1. 通过 `ToolManager` 根据 `toolName` 找到实际工具。
2. 解析工具参数为 `JSONObject`。
3. 调用工具自己的 `generateToolRequestResponse(...)` 和 `generateToolExecutedResult(...)`。
4. 将结果写入可读流文本：
   - `[工具调用] ...`
   - `[工具完成] ...`

### 这一改动带来的实际效果

前端消息区和聊天记录落库内容，不再只会看到“写文件成功”，而是能看到更完整的过程，例如：

- 正在读取目录结构
- 已读取文件
- 正在修改文件
- 已删除文件

这意味着工具调用过程从“机器内部动作”变成了“用户可理解的修改轨迹”。

---

## 8. Prompt 改动详解

## 8.1 `src/main/resources/prompt/codegen-single-file-system-prompt.txt`

### 改动内容

在原始单文件生成 prompt 中新增“可视化修改场景”约束，明确：

- 若消息中出现“选中元素信息”和“修改需求”，必须优先根据这些信息定位目标元素。
- 只能修改最小必要代码。
- 禁止无关重构和无关删除。

### 作用

即使没有走修改专用接口，只要用户消息带有明确可视化上下文，单文件模式也会比之前更保守，不再轻易把局部修改放大为全页重写。

---

## 8.2 `src/main/resources/prompt/codegen-multi-file-system-prompt.txt`

### 改动内容

新增“可视化修改场景”约束，明确：

- 优先按选中元素信息定位范围
- 只改必要文件
- 只改必要内容
- 改文案优先改 HTML
- 改样式优先改 CSS

### 作用

多文件模式最常见的问题是“一句话改动牵连 HTML/CSS/JS 三个文件一起重吐”。新增约束后，模型会更倾向于在真正必要的文件内完成局部修改。

---

## 8.3 修改专用 prompt 文件

新增 3 个修改专用 prompt：

- `src/main/resources/prompt/codegen-single-file-modify-system-prompt.txt`
- `src/main/resources/prompt/codegen-multi-file-modify-system-prompt.txt`
- `src/main/resources/prompt/codegen-vue-project-modify-system-prompt.txt`

### 单文件修改 prompt 的重点

- 输出仍必须是完整 HTML
- 但修改范围必须最小化
- 文案、颜色、尺寸、图片等局部调整时尽量保持结构不变

### 多文件修改 prompt 的重点

- 优先依据选中元素信息锁定范围
- 改文案优先 `index.html`
- 改样式优先 `style.css`
- 无交互需求尽量不改 `script.js`

### Vue 工程修改 prompt 的重点

- 只能通过工具修改现有工程
- 先读目录再读文件，禁止盲写
- 优先用 `modifyFile`
- 禁止删除关键骨架文件
- 不允许整项目重写

这三个 prompt 的意义在于：创建场景和修改场景终于不再共享同一套语言约束，而是分别围绕“构建新页面”和“精准修补已有页面”来组织 AI 行为。

---

## 8.4 `src/main/resources/prompt/codegen-vue-project-system-prompt.txt`

### 改动内容

原来这个 prompt 只强调 `writeFile`。本阶段把它扩展为支持：

- `readDir`
- `readFile`
- `modifyFile`
- `writeFile`
- `deleteFile`

并补充说明：

- 在无需修改已有文件时避免多余工具调用。

### 作用

这样即使在“创建 Vue 工程”的场景里，模型的工具认知也已经与当前工具集保持一致，避免 service 里注入了整套工具，但 prompt 还停留在旧时代的“只能写文件”。

---

## 9. 测试与验证改动详解

## 9.1 新增与扩展的后端测试文件

### `src/test/java/com/adcage/acaicodefree/core/VisualEditPromptAssemblyTest.java`

验证“什么样的用户消息会被识别为可视化修改请求”。

这个测试不是测 UI，而是测规则边界：

- 包含“选中元素信息 + 修改需求” -> 应识别为修改请求
- 普通描述性 prompt -> 不应误判

### `src/test/java/com/adcage/acaicodefree/ai/tools/ToolManagerTest.java`

验证：

- 工具是否能按 `toolName` 正确注册和查找
- `getAllTools()` 是否能导出完整工具数组
- 重复工具名是否会被拒绝，防止运行时歧义

### `src/test/java/com/adcage/acaicodefree/ai/tools/FileModifyToolTest.java`

覆盖两类关键场景：

- 命中旧内容时成功替换
- 未命中旧内容时不强写，只返回失败文案

这个测试保障的是“修改工具不会盲改文件”。

### `src/test/java/com/adcage/acaicodefree/ai/tools/FileDeleteToolTest.java`

覆盖：

- 普通文件可删除
- 关键文件不可删除

这个测试直接对应本阶段文档里强调的“关键文件保护边界”。

### `src/test/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandlerTest.java`

改造成使用 `ToolManager`，验证工具请求与执行结果能够被转成统一的 `[工具调用]` / `[工具完成]` 文案，而不是只测试旧的写文件路径解析逻辑。

### `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeTest.java`

新增了可视化修改请求下的路由测试，确认：

- 单文件模式下会走 `modifySingleFileCodeStream`
- Vue 工程模式下会走 `modifyVueProjectCodeStream`

### `src/test/java/com/adcage/acaicodefree/core/AiCodeGeneratorFacadeStreamMessageTest.java`

增加修改场景流式消息测试，确认修改模式下依然会正确输出：

- `ai_response`
- `tool_request`
- `tool_executed`

这说明修改链路没有破坏原有 Vue 工程模式的流消息契约。

### `src/test/java/com/adcage/acaicodefree/controller/AppChatE2ETest.java`

这个后端端到端测试文件在本阶段继续承担完整链路验证职责，覆盖：

- 聊天会话创建
- SSE 返回结构
- 工具消息转译
- 历史消息持久化
- Vue 模式下工具消息可读化落库

---

## 9.2 前端端到端测试文件

### `ac-ai-code-free-fronted/tests/chat-flow.e2e.test.mjs`

在原有聊天链路测试基础上，新增了“可视化选区上下文修改请求可通过”的端到端场景。

这个测试虽然不直接驱动浏览器点击 iframe，但它验证了非常关键的一点：

- 当前端把“选中元素信息 + 修改需求”这类增强 prompt 发往后端时，整条前后端链路依然可以成功完成：注册、登录、建应用、建会话、SSE 输出、历史查询、下载源码。

换句话说，它验证的是“可视化上下文格式已经能稳定进入现有聊天链路”，而不是停留在前端 UI 层面。

---

## 10. 本阶段完成后，系统行为发生了哪些实质性变化

这一阶段的价值，不在于多了一个“编辑模式按钮”，而在于系统修改行为的底层范式发生了变化。

### 10.1 从“描述一个大概位置”变成“明确选择一个具体元素”

改造前，用户说“把这里改成红色”“改第二个卡片标题”，模型只能靠猜。

改造后，系统会明确告诉模型：

- 当前改的是哪个页面
- 当前改的是哪个标签
- 当前改的是哪条 selector 链路
- 当前文字内容是什么

这直接提高了局部修改命中率。

### 10.2 从“所有模式都像重新生成”变成“创建与修改分离”

改造前，系统虽然名义上支持继续对话修改，但底层依然更像“根据最新一句话重新生成”。

改造后：

- 原生模式通过更保守的 prompt 收缩改动范围。
- Vue 模式通过修改专用 prompt 和工具集走真正的增量修改链路。

### 10.3 从“工具能执行”变成“工具过程可观察、可理解”

以前用户看到的工具过程很贫瘠。

现在，用户和历史记录都能看到更具体的过程：

- 哪个目录被读取了
- 哪个文件被读取了
- 哪个文件被修改了
- 哪个文件被删除了

这会显著提升用户对 AI 修改过程的可解释性和信任感。

### 10.4 从“Vue 项目只能重写”变成“具备增量修改能力”

这一点是本阶段最重要的后端能力升级。Vue 工程模式现在已经具备：

- 目录认知
- 文件读取
- 局部替换
- 安全删除
- 覆盖写入

这意味着平台开始具备对真实工程做细粒度修改的基础，而不再只能依赖粗放式整项目输出。

---

## 11. 验证结果

本阶段严格按照“先写完所有代码，再统一验证”的方式执行，没有在每改完一个文件后频繁跑编译。

### 后端测试命令

```bash
mvn test -Dtest=VisualEditPromptAssemblyTest,ToolManagerTest,FileModifyToolTest,FileDeleteToolTest,JsonMessageStreamHandlerTest,AiCodeGeneratorFacadeTest,AiCodeGeneratorFacadeStreamMessageTest,AiCodeGenServiceFactoryTest,AppChatE2ETest
```

### 后端测试结果

- `BUILD SUCCESS`
- `Tests run: 30, Failures: 0, Errors: 0, Skipped: 0`

### 前端类型检查与构建命令

```bash
npm run type-check && npm run build-only
```

### 前端验证结果

- `vue-tsc` 类型检查通过
- `vite build` 构建通过
- 仅存在 chunk size warning，不影响构建成功

### 前后端端到端测试命令

```bash
npm run test:e2e:chat
```

### 前后端端到端测试结果

3 个测试场景全部通过：

1. 登录 -> 应用 -> 会话 -> SSE -> 历史 基础链路
2. Vue 工程模式 SSE 二层消息契约兼容
3. 可视化选区上下文修改请求可通过

---

## 12. 本阶段的边界与后续可继续优化点

虽然第九阶段主链路已经完成，但当前实现仍然保留了几个可继续优化的方向：

### 12.1 当前的可视化选择器更偏“AI 可读”，不是“浏览器精确重放”

这是有意设计的。当前 selector 更强调可理解性，而不是 100% 精确的 DOM 重放。如果未来要做更深层的编辑能力，可以再引入更稳定的定位标记体系。

### 12.2 当前前端 e2e 主要验证上下文链路，而不是浏览器级真实点选

现有前端 e2e 已验证增强 prompt 能从前端进入后端链路，但还没有上浏览器自动化去真实模拟 iframe 内选中行为。如果后续要做更强 UI 回归，可再引入 Playwright 类测试。

### 12.3 `modifyFile` 目前是字符串替换，不是 AST 级改动

这是当前阶段最符合成本与收益平衡的实现。后续若遇到结构性修改场景较多，可以进一步演进成更语义化的修改方式。

---

## 13. 总结

第九阶段已经不再是“平台会继续聊天修改网站”这么简单，而是建立了一套真正可用的“可视化选区 -> 提示词增强 -> 后端局部执行 -> 工具过程展示 -> 全链路验证”的闭环。

它带来的最大变化不是视觉上多了一个按钮，而是修改这件事从“模糊描述 + AI 猜位置”，升级成了“用户明确指出目标 + 系统把目标上下文结构化传给 AI + 后端按场景选择最合适的保守修改策略”。

对平台来说，这标志着能力从“会生成”进一步走向“会精确地改”。
