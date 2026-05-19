# 项目简历 — ac-ai-code-free

## 项目名称

**AC AI Code Free — AI 智能编程辅助平台**

## 项目简介

基于 Spring Boot 3 + Vue 3 的 AI 编程辅助平台，用户通过自然语言描述需求，AI 自动生成前端代码并实时预览。支持单文件/多文件/Vue 工程三种生成模式，具备流式对话、可视化编辑、一键部署与源码下载能力，实现了从"需求描述→代码生成→实时预览→在线编辑→部署上线"的全链路闭环。

## 技术栈

**后端**：Java 21 / Spring Boot 3.5.5 / MyBatis-Flex / LangChain4j 0.36.2 / Caffeine / Redis / Selenium / 腾讯云 COS / Knife4j

**前端**：Vue 3 / TypeScript / Vite 7 / Ant Design Vue / Pinia / Axios

**AI 模型**：DeepSeek Chat / DeepSeek Reasoner / MiniMax M2.7

**数据库**：MySQL 5.7+

## 核心职责与技术亮点

### 1. AI 代码生成引擎设计（Facade + 策略 + 模板方法）

- 设计 `AiCodeGeneratorFacade` 门面层统一编排 AI 生成与文件保存流程，对上层屏蔽底层复杂性
- 采用策略模式实现流式消息处理器（`JsonMessageStreamHandler` / `SimpleTextStreamHandler`），按代码生成类型动态切换处理逻辑
- 采用模板方法模式设计 `AbstractCodeFileSaver`，定义"验证→建目录→保存"标准流程，子类仅实现差异化保存逻辑
- 基于 LangChain4j 声明式接口定义 6 个 AI 服务方法（3 种类型 × 生成/修改），通过 `AiServices.builder()` 动态构建实例，配合 Caffeine 缓存（key=appId:codeGenType，写入 30min 过期）避免重复创建

### 2. AI 工具调用系统与安全防护

- 设计 5 个文件操作工具（readFile / writeFile / modifyFile / deleteFile / readDir），通过 `ToolManager` 统一注册管理，AI 可自主调用完成 Vue 工程级代码生成
- 实现路径穿越防护：所有工具通过 `resolveRelativePath()` 对 normalize 后路径校验是否仍在项目根目录内
- 实现 FileDeleteTool 关键文件保护机制，禁止 AI 删除 `package.json`、`vite.config.*`、`src/main.*` 等工程核心文件
- 设计流消息协议（ai_response / tool_request / tool_executed 三种消息类型），前端可实时展示 AI 思考过程与工具调用事件

### 3. SSE 流式对话与实时预览

- 后端基于 Reactor `Flux<ServerSentEvent>` 实现流式代码生成接口，TokenStream 逐 token 推送，首字响应时间 < 1s
- 前端使用原生 EventSource 接收 SSE 流，实现打字机效果实时渲染 AI 输出
- 设计流式聚合保存机制：StringBuilder 在流结束后聚合完整内容，再解析代码块并写入文件，确保文件完整性
- Vue 工程模式流结束后自动触发 `npm install + npm run build`，支持依赖版本自动修复

### 4. 可视化编辑系统

- 设计 iframe 注入式可视化编辑器：通过 `postMessage` 双向通信，IIFE 脚本注入实现元素悬浮高亮（蓝色虚线）与点击选中（绿色实线高亮）
- 实现 CSS 选择器自动构建算法（标签+类+nth-of-type，最多 8 层深度），选中元素信息自动拼接到用户 prompt
- 设计创建/修改分流机制：通过 `VisualEditPromptHelper` 判断消息是否同时包含"选中元素信息"和"修改需求"，自动路由到修改专用 AI 接口，使用差异化 Prompt 实现增量修改而非全量重生成

### 5. AI 智能路由

- 实现 `AiCodeGenTypeRoutingService` 声明式接口，AI 自动分析用户 Prompt 判断应使用的代码生成类型
- 三级优先级策略：显式指定 > AI 路由 > 默认兜底（MULTI_FILE），兼顾灵活性与可靠性

### 6. 全链路工程能力

- **自动封面图**：Selenium 无头浏览器截图 + 图片压缩 + COS 上传 + 异步回写，串行执行器 + 虚拟线程，支持状态观测与失败重试
- **源码下载**：自动排除 `node_modules`/`dist`/`.env` 等目录，ZIP 压缩后写入 HTTP 响应流
- **一键部署**：生成 6 位唯一 deployKey，复制 dist 到部署目录，静态资源映射即可访问
- **多模型配置**：标准任务使用 DeepSeek Chat，Vue 工程推理使用 DeepSeek Reasoner，开发环境使用 MiniMax M2.7

### 7. 前端架构与工程化

- 基于 `@umijs/openapi` 从后端 OpenAPI 规范自动生成 TypeScript 类型和 API 调用函数，前后端类型零手工维护
- 路由自动发现：`import.meta.glob` 自动加载路由模块，新增页面无需手动注册
- Ant Design Vue 响应式布局，支持桌面端/移动端预览切换
- 可拖拽面板布局（对话区 + 预览区），提升交互体验

## 项目成果

- 实现了 3 种代码生成模式（单文件 / 多文件 / Vue 工程）的完整闭环，覆盖从需求描述到部署上线的全流程
- AI 工具调用系统支持 5 种文件操作，Vue 工程模式下 AI 可自主创建完整前端项目
- 流式对话首字响应 < 1s，用户可实时看到 AI 生成过程
- 可视化编辑实现"选中即修改"，将 AI 编程从"全量生成"升级为"精准修改"
- 后端 108 个 Java 源文件，前端 33 个源文件，代码结构清晰，设计模式运用合理

## 项目规模

- 后端：108 个 Java 源文件，32 个 API 接口，4 张数据库表
- 前端：33 个源文件，8 个页面，14 个 Vue 组件
- AI：8 个系统 Prompt 模板，6 个声明式 AI 服务方法，5 个工具
