# ac-ai-code-free 项目完整分析报告

## 一、项目概述

**ac-ai-code-free** 是一个基于 Spring Boot 3.5.5 + Vue 3 的 **AI 编程辅助平台**，用户通过自然语言描述需求，AI 自动生成前端代码（单文件/多文件/Vue 工程），支持流式对话、实时预览、可视化编辑、一键部署和源码下载。

- **许可证**：MIT (Copyright 2025 Adcage)
- **架构**：前后端分离，Cookie-based 认证
- **后端端口**：8700（context-path: `/api`）| **前端端口**：5173
- **API 文档**：`http://localhost:8080/doc.html`（Knife4j）

---

## 二、技术栈

### 2.1 后端 (Java 21)

| 组件 | 版本 | 用途 |
|------|------|------|
| Spring Boot | 3.5.5 | Web 框架 |
| MyBatis-Flex | 1.11.0 | ORM 框架 |
| LangChain4j | 0.36.2 | AI 集成（声明式接口 + 流式 + 工具调用） |
| Caffeine | - | AI 服务实例缓存 |
| Spring Data Redis | - | 缓存（已引入，Phase 11 待用） |
| Knife4j | 4.4.0 | API 文档 |
| Selenium | 4.33.0 | 网页截图（封面图生成） |
| 腾讯云 COS | 5.6.227 | 文件存储 |
| Hutool | 5.8.38 | 工具库 |
| Lombok | 1.18.38 | 代码简化 |

### 2.2 前端 (Node ^20.19.0 \|\| >=22.12.0)

| 组件 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5.18 | 前端框架 |
| TypeScript | 5.8 | 类型安全 |
| Vite | 7.0.6 | 构建工具 |
| Ant Design Vue | 4.2.6 | UI 组件库 |
| Pinia | 3.0.3 | 状态管理 |
| Axios | 1.11.0 | HTTP 请求 |
| dayjs | 1.11.18 | 时间处理 |

### 2.3 AI 模型配置

| 环境 | 默认模型 | Vue 工程模型 |
|------|----------|-------------|
| 开发 | minimax-m2.7 (via opencode.ai 代理) | deepseek-chat |
| 生产 | deepseek-chat | deepseek-reasoner |

---

## 三、数据库设计（4 张表）

### 3.1 user 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键，雪花 ID |
| userAccount | String | 账号（唯一） |
| userPassword | String | 密码（MD5 加密） |
| userName | String | 用户昵称 |
| userAvatar | String | 用户头像 URL |
| userProfile | String | 用户简介 |
| userRole | String | 角色：user/admin |
| vipExpireTime | LocalDateTime | 会员过期时间 |
| vipCode | String | 会员兑换码 |
| vipNumber | Long | 会员编号 |
| shareCode | String | 分享码 |
| inviteUser | Long | 邀请用户 ID |

索引：`uk_userAccount`, `idx_userName`

### 3.2 app 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键，雪花 ID |
| appName | String | 应用名称 |
| cover | String | 应用封面 URL |
| initPrompt | String | 初始化提示词（max 8192） |
| codeGenType | String | 代码生成类型（single_file/multi-file/vue_project） |
| deployKey | String | 部署标识（6 位随机字符串，唯一） |
| deployedTime | LocalDateTime | 部署时间 |
| priority | Integer | 优先级（99=精选，0=默认） |
| userId | Long | 创建用户 ID |

索引：`uk_deployKey`, `idx_appName`, `idx_userId`

### 3.3 chat_session 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键 |
| appId | Long | 应用 ID |
| userId | Long | 用户 ID |
| title | String | 会话标题 |
| messageCount | Integer | 消息数 |
| modelName | String | 模型名称（实际存储 codeGenType） |
| lastMessageTime | LocalDateTime | 最后消息时间 |

索引：`idx_userId_appId_updateTime`, `idx_appId_lastMessageTime`

### 3.4 chat_history 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键 |
| sessionId | Long | 会话 ID |
| seqNo | Integer | 消息序号（从 1 递增） |
| message | MEDIUMTEXT | 消息内容（最大 16MB） |
| messageType | String | 消息类型：user/ai/system/tool |
| status | String | 状态：success/failed |
| appId | Long | 应用 ID |
| userId | Long | 用户 ID |
| inputTokens | Integer | 输入 token 数 |
| outputTokens | Integer | 输出 token 数 |
| latencyMs | Integer | 响应耗时(ms) |
| requestId | String | 请求追踪 ID |
| extra | JSON | 扩展字段（错误信息、工具调用等） |

索引：`uk_sessionId_seqNo`, `idx_sessionId_createTime`, `idx_appId_createTime`

---

## 四、后端架构详解

### 4.1 目录结构

```
src/main/java/com/adcage/acaicodefree/
├── AcAICodeFreeApplication.java          # Spring Boot 启动类
├── ai/                                   # AI 集成层
│   ├── AiCodeGeneratorService.java       # AI 代码生成声明式服务接口
│   ├── AiCodeGenServiceFactory.java      # AI 服务工厂（Caffeine 缓存）
│   ├── AiCodeGenTypeRoutingService.java  # AI 路由声明式接口
│   ├── AiCodeGenTypeRoutingServiceFactory.java
│   ├── model/
│   │   ├── SingleCodeResult.java         # 单文件代码结果
│   │   ├── MultiFileCodeResult.java      # 多文件代码结果
│   │   └── message/
│   │       ├── StreamMessage.java        # 流消息基类
│   │       ├── StreamMessageTypeEnum.java
│   │       ├── AiResponseMessage.java    # AI 响应消息
│   │       ├── ToolRequestMessage.java   # 工具请求消息
│   │       └── ToolExecutedMessage.java  # 工具执行结果消息
│   └── tools/
│       ├── BaseTool.java                 # 工具基类（抽象类）
│       ├── ToolManager.java              # 工具管理器
│       ├── FileReadTool.java             # 文件读取工具
│       ├── FileWriteTool.java            # 文件写入工具
│       ├── FileModifyTool.java           # 文件修改工具
│       ├── FileDeleteTool.java           # 文件删除工具
│       └── FileDirReadTool.java          # 目录读取工具
├── annotation/
│   └── AuthCheck.java                    # 权限校验注解
├── aop/
│   ├── AuthInterceptor.java              # 权限校验切面
│   └── LogInterceptor.java               # 请求日志切面
├── common/
│   ├── BaseResponse.java                 # 统一响应封装
│   ├── CommonConstant.java
│   ├── DeleteRequest.java
│   ├── ErrorCode.java                    # 错误码枚举
│   ├── PageRequest.java
│   └── ResultUtils.java
├── config/
│   ├── CorsConfig.java                   # CORS 跨域配置
│   ├── CosClientConfig.java              # 腾讯云 COS 客户端配置
│   ├── JsonConfig.java                   # Jackson 序列化配置（Long→String）
│   ├── ReasoningStreamingChatModelConfig.java
│   ├── ScreenshotConfig.java
│   ├── StorageConfig.java
│   ├── WebMvcConfig.java                 # 静态资源映射
│   └── properties/
│       ├── CosClientProperties.java
│       ├── ScreenshotProperties.java
│       └── StorageProperties.java
├── constant/
│   ├── AppConstant.java
│   └── UserConstant.java
├── controller/
│   ├── AppController.java                # 应用控制器（18 个接口）
│   ├── HealthController.java             # 健康检查
│   └── UserController.java               # 用户控制器（13 个接口）
├── core/                                 # 核心业务编排层
│   ├── AiCodeGeneratorFacade.java        # AI 代码生成门面（Facade）
│   ├── VisualEditPromptHelper.java       # 可视化编辑辅助
│   ├── build/
│   │   └── VueProjectBuildService.java   # Vue 项目构建服务
│   ├── handler/
│   │   ├── JsonMessageStreamHandler.java # JSON 消息流处理器
│   │   ├── SimpleTextStreamHandler.java  # 简单文本流处理器
│   │   └── StreamHandlerExecutor.java    # 流处理器执行器（策略调度）
│   ├── memory/
│   │   └── ChatMemoryLoader.java         # 聊天记忆加载器
│   ├── parser/
│   │   ├── CodePaser.java                # 代码解析策略接口
│   │   ├── CodeParserExcutor.java        # 解析执行器
│   │   ├── MultiFileParser.java          # 多文件解析策略
│   │   └── SingleFileParser.java         # 单文件解析策略
│   └── saver/
│       ├── AbstractCodeFileSaver.java    # 保存模板方法（抽象类）
│       ├── CodeFileSaverExecutor.java    # 保存执行器
│       ├── MultiCodeFileSaver.java       # 多文件保存实现
│       └── SingleCodeFileSaver.java      # 单文件保存实现
├── exception/
│   ├── BusinessException.java
│   ├── GlobalExceptionHandler.java
│   └── ThrowUtils.java
├── generator/
│   └── MyBatisCodegen.java               # MyBatis-Flex 代码生成器
├── manager/
│   └── CosManager.java                   # COS 文件管理器
├── mapper/
│   ├── AppMapper.java
│   ├── ChatHistoryMapper.java
│   ├── ChatSessionMapper.java
│   └── UserMapper.java
├── model/
│   ├── dto/
│   │   ├── app/ (5 个 DTO)
│   │   ├── chat/ (2 个 DTO)
│   │   └── user/ (6 个 DTO)
│   ├── entity/ (4 个实体)
│   ├── enums/ (3 个枚举)
│   └── vo/ (6 个 VO)
├── service/
│   ├── AppService.java
│   ├── ProjectDownloadService.java
│   ├── ScreenshotService.java
│   ├── UserService.java
│   └── impl/
│       ├── AppServiceImpl.java           # 最核心服务（698 行）
│       ├── ProjectDownloadServiceImpl.java
│       ├── ScreenshotServiceImpl.java
│       └── UserServiceImpl.java
├── storage/
│   ├── FileStorageStrategy.java          # 存储策略接口
│   └── impl/
│       ├── CosStorageStrategy.java       # COS 存储实现
│       └── LocalStorageStrategy.java     # 本地存储实现
└── utils/
    ├── WebDriverFactory.java
    └── WebScreenshotUtils.java
```

### 4.2 核心业务流程

```
用户消息 → AppController.chatToGenCode (SSE)
  → AppServiceImpl.chatToGenCode
    → 保存用户消息到 chat_history
    → AiCodeGeneratorFacade.generateAndSaveCodeStream
      → AiCodeGenServiceFactory (Caffeine 缓存, key=appId:codeGenType)
        → AiServices.builder 动态构建 (工具 + 记忆)
      → AiCodeGeneratorService 声明式接口 (8 个 AI 方法)
        → AI 流式输出 + 工具调用事件
      → StreamHandlerExecutor (策略选择)
        → VUE_PROJECT → JsonMessageStreamHandler
        → SINGLE/MULTI_FILE → SimpleTextStreamHandler
      → CodeFileSaverExecutor (流式聚合 → 解析 → 保存)
      → [VUE_PROJECT] VueProjectBuildService (npm install + build)
    → 保存 AI 消息到 chat_history
  → SSE 返回 (meta → data... → done)
```

### 4.3 设计模式使用

| 模式 | 应用位置 | 说明 |
|------|----------|------|
| **Facade** | `AiCodeGeneratorFacade` | 统一 AI 生成 + 保存入口，隐藏内部复杂性 |
| **策略** | `StreamHandlerExecutor` | 按 codeGenType 选择流处理器 |
| **策略** | `CodeParserExcutor` | 按 codeGenType 选择代码解析器 |
| **策略** | `FileStorageStrategy` | 按 storage.type 选择存储实现 |
| **模板方法** | `AbstractCodeFileSaver` | 验证→建目录→保存，子类实现具体保存逻辑 |
| **工厂** | `AiCodeGenServiceFactory` | 动态创建 AI 服务实例（含 Caffeine 缓存） |
| **工厂** | `AiCodeGenTypeRoutingServiceFactory` | 动态创建 AI 路由服务实例 |
| **观察者** | SSE + Reactor Flux | 流式事件推送 |

### 4.4 AI 集成详解

#### 4.4.1 AI 声明式服务接口 — 8 个方法

| 方法 | 类型 | Prompt 文件 |
|------|------|------------|
| generateSingleFileCodeStream | 单文件生成 | codegen-single-file-system-prompt.txt |
| modifySingleFileCodeStream | 单文件修改 | codegen-single-file-modify-system-prompt.txt |
| generateMultiFileCodeStream | 多文件生成 | codegen-multi-file-system-prompt.txt |
| modifyMultiFileCodeStream | 多文件修改 | codegen-multi-file-modify-system-prompt.txt |
| generateVueProjectCodeStream | Vue 工程生成 | codegen-vue-project-system-prompt.txt |
| modifyVueProjectCodeStream | Vue 工程修改 | codegen-vue-project-modify-system-prompt.txt |

此外还有 `AiCodeGenTypeRoutingService` 用于 AI 智能路由，prompt 来自 `codegen-routing-system-prompt.txt`。

#### 4.4.2 AI 服务工厂 — 缓存机制

- 缓存 key：`appId:codeGenType`
- 最大容量：1000 条
- 写入过期：30 分钟
- 访问过期：10 分钟
- VUE_PROJECT 模式使用 `reasoningStreamingChatModel`（推理模型），其他使用标准流式模型

#### 4.4.3 AI 智能路由

优先级：**显式指定 > AI 路由 > 默认兜底（MULTI_FILE）**

用户在创建应用时可指定 codeGenType，若未指定则由 AI 分析 initPrompt 自动判断应使用哪种生成类型。

#### 4.4.4 AI 工具集

| 工具 | 方法签名 | 安全机制 |
|------|----------|----------|
| FileReadTool | `readFile(relativeFilePath, appId, codeGenType)` | 路径穿越检查（normalize 后校验仍在项目根内） |
| FileWriteTool | `writeFile(relativeFilePath, content, appId, codeGenType)` | 路径穿越检查 |
| FileModifyTool | `modifyFile(relativeFilePath, oldContent, newContent, appId, codeGenType)` | 路径穿越检查 |
| FileDeleteTool | `deleteFile(relativeFilePath, appId, codeGenType)` | 路径穿越检查 + 保护关键文件 |
| FileDirReadTool | `readDir(relativeDirPath, appId, codeGenType)` | 路径穿越检查 |

**FileDeleteTool 受保护文件**：`package.json`, `vite.config.js/ts`, `tsconfig.json`, `.gitignore`, `src/main.js/ts`, `src/app.vue` 等

**ToolManager**：`@PostConstruct` 初始化时收集所有 BaseTool 实现，按 toolName 注册到 Map，检测重复工具名。

#### 4.4.5 流消息协议

| 消息类型 | type 字段 | 内容 |
|----------|-----------|------|
| AiResponseMessage | `ai_response` | data = token 文本 |
| ToolRequestMessage | `tool_request` | id, name, arguments |
| ToolExecutedMessage | `tool_executed` | id, name, arguments, result |

### 4.5 API 接口完整清单

#### AppController（18 个接口）

| HTTP 方法 | 路径 | 功能 | 权限 |
|-----------|------|------|------|
| POST | `/app/add` | 创建应用 | 登录用户 |
| GET | `/app/download/{appId}` | 下载应用源码 ZIP | 仅本人 |
| POST | `/app/delete` | 删除应用 | 本人或管理员 |
| POST | `/app/edit` | 编辑应用（仅 appName） | 仅本人 |
| GET | `/app/get/vo` | 获取应用 VO 详情 | 无限制 |
| POST | `/app/my/list/page/vo` | 分页查询我的应用 | 登录用户 |
| POST | `/app/good/list/page/vo` | 分页查询精选应用 | 无限制 |
| GET | `/app/chat/gen/code/stream` | SSE 流式 AI 对话生成代码 | 登录用户 |
| POST | `/app/chat/session/create` | 创建对话会话 | 登录用户 |
| GET | `/app/chat/session/list` | 查询应用下会话列表 | 登录用户 |
| POST | `/app/chat/history/page` | 分页查询会话消息 | 登录用户 |
| POST | `/app/deploy` | 部署应用 | 仅本人 |
| POST | `/app/update` | 管理员更新应用 | 管理员 |
| POST | `/app/delete/admin` | 管理员删除应用 | 管理员 |
| GET | `/app/get` | 管理员获取应用原始数据 | 管理员 |
| GET | `/app/admin/get/vo` | 管理员获取应用 VO | 管理员 |
| POST | `/app/admin/list/page/vo` | 管理员分页查询应用 VO | 管理员 |
| POST | `/app/list/page` | 管理员分页查询原始数据 | 管理员 |

#### UserController（13 个接口）

| HTTP 方法 | 路径 | 功能 | 权限 |
|-----------|------|------|------|
| POST | `/user/register` | 用户注册 | 无限制 |
| POST | `/user/login` | 用户登录 | 无限制 |
| GET | `/user/get/login` | 获取当前登录用户 | 登录用户 |
| POST | `/user/logout` | 用户注销 | 登录用户 |
| POST | `/user/add` | 管理员创建用户 | 管理员 |
| GET | `/user/get` | 管理员获取用户原始数据 | 管理员 |
| GET | `/user/get/vo` | 获取用户 VO | 管理员 |
| POST | `/user/delete` | 管理员删除用户 | 管理员 |
| POST | `/user/multi/delete` | 管理员批量删除用户 | 管理员 |
| POST | `/user/update` | 管理员更新用户 | 管理员 |
| POST | `/user/edit/user/self` | 用户编辑自身信息 | 登录用户 |
| POST | `/user/list/page/vo` | 分页查询用户 VO 列表 | 无限制 |
| POST | `/user/list/page` | 管理员分页查询用户原始数据 | 管理员 |

#### HealthController（1 个接口）

| HTTP 方法 | 路径 | 功能 | 权限 |
|-----------|------|------|------|
| GET | `/health/check` | 健康检查（返回 "ok"） | 无限制 |

### 4.6 配置类说明

| 配置类 | 功能 | 关键逻辑 |
|--------|------|----------|
| `CorsConfig` | CORS 跨域 | 允许所有域名，支持 Cookie |
| `JsonConfig` | Jackson 序列化 | Long→String，防止前端精度丢失 |
| `WebMvcConfig` | 静态资源映射 | `/static/**` → code_output/ + code_deploy/ |
| `CosClientConfig` | COS 客户端 | 仅 `storage.type=cos` 时激活 |
| `StorageConfig` | 本地存储 | 仅 `storage.type=local` 时激活 |
| `ReasoningStreamingChatModelConfig` | 推理模型 | 按 profile 选择 dev/prod 模型 |

### 4.7 应用配置

| 配置项 | 值 | 说明 |
|--------|------|------|
| `server.port` | 8700 | 服务端口 |
| `server.servlet.context-path` | /api | API 上下文路径 |
| `server.servlet.session.timeout` | 1d | Session 超时 1 天 |
| `langchain4j.open-ai.chat-model.model-name` | deepseek-chat | 默认对话模型 |
| `langchain4j.open-ai.streaming-chat-model.model-name` | deepseek-chat | 默认流式模型 |
| `app.ai.vue-project.memory-window-size` | 20 | 聊天记忆窗口大小 |
| `app.ai.vue-project.install-timeout-seconds` | 300 | npm install 超时 |
| `app.ai.vue-project.build-timeout-seconds` | 180 | npm build 超时 |
| `storage.type` | cos（默认）/ local | 存储类型 |

---

## 五、前端架构详解

### 5.1 目录结构

```
ac-ai-code-free-fronted/src/
├── access/           # 路由守卫（3 个文件）
│   ├── index.ts      # 自动加载守卫模块
│   ├── access.ts     # 全局前置守卫
│   └── router_access.ts  # 重复的守卫（待清理）
├── api/              # 自动生成的 API 层（5 个文件，勿手动编辑）
│   ├── appController.ts
│   ├── userController.ts
│   ├── healthController.ts
│   └── typings.d.ts  # 372 行，约 40 个类型定义
├── assets/           # 静态资源
│   └── background.png
├── components/       # 公共组件（5 个）
│   ├── AppCard.vue       # 应用卡片（317 行）
│   ├── AppEditModal.vue  # 应用编辑弹窗（196 行）
│   ├── GlobalHeader.vue  # 全局头部导航（216 行）
│   ├── GlobalFooter.vue  # 全局页脚（77 行，未使用）
│   ├── UserAvatar.vue    # 用户头像（32 行）
│   └── common/           # 空目录
├── layouts/
│   └── BasicLayout.vue   # 基础布局（31 行）
├── pages/            # 页面组件（8 个）
│   ├── HomePage.vue           # 首页（281 行）
│   ├── MyAppListPage.vue      # 我的作品（138 行）
│   ├── AppGeneratorPage.vue   # 核心页面：AI 对话生成器（1354 行）
│   ├── AppEditPage.vue        # 应用编辑（99 行）
│   ├── admin/
│   │   ├── AppAdminPage.vue   # 应用管理（284 行）
│   │   └── UserManagePage.vue # 用户管理（280 行）
│   └── user/
│       ├── UserLoginPage.vue     # 登录（121 行）
│       └── UserRegisterPage.vue  # 注册（129 行）
├── router/           # 路由配置（5 个 .ts，自动发现）
├── stores/           # Pinia 状态管理（2 个）
│   ├── LoginUser.ts  # 登录用户状态
│   └── counter.ts    # 脚手架残留
├── utils/
│   └── visualEditor.ts  # 可视化编辑器（435 行）
├── App.vue           # 根组件
├── main.ts           # 入口文件
└── request.ts        # Axios 实例
```

### 5.2 核心页面 — AppGeneratorPage

这是项目最复杂最核心的页面（1354 行），包含：

**左侧对话区**：
- 会话管理：加载/创建/切换会话
- 消息列表：区分用户/AI 消息，简易 Markdown 渲染
- 工具调用展示：折叠展示 writeFile/readFile/modifyFile/deleteFile/readDir 事件
- SSE 流式对话：使用原生 EventSource 连接后端 SSE 端点
- 选中元素提示：可视化编辑模式下自动拼接元素信息

**右侧预览区**：
- iframe 预览生成的页面，支持桌面端/移动端切换
- 可视化编辑模式：通过 `visualEditor.ts` 注入脚本实现悬浮高亮、点击选中
- 部署状态检测：iframe 加载后检测错误页面

**顶部操作栏**：
- 返回、部署、下载源码
- 封面任务状态展示（PENDING/RUNNING/SUCCESS/FAILED/SKIPPED）
- 代码生成类型标签

**面板可拖拽调整**：中间分割线支持鼠标拖拽调整左右面板宽度

### 5.3 可视化编辑器 (visualEditor.ts)

- 通过 `postMessage` 在父页面和 iframe 之间通信
- `buildInjectedScript()` 生成 IIFE 脚本注入到 iframe DOM
- 悬浮蓝色虚线高亮，选中绿色实线高亮
- 构建 CSS 选择器（标签+类+nth-of-type，最多 8 层深度）
- 收集元素信息（标签、选择器、文本内容、位置尺寸）
- 暴露 API：`enterEditMode()`, `exitEditMode()`, `clearSelection()`, `handleIframeLoad()`, `dispose()`

### 5.4 状态管理

| Store | 状态 | 方法 |
|-------|------|------|
| `LoginUser` | loginUser | fetchLoginUser, setLoginUser, logout |
| `counter` | count（脚手架残留） | increment |

### 5.5 路由配置

| 路径 | 名称 | 组件 | 守卫 |
|------|------|------|------|
| `/` | 主页 | HomePage | - |
| `/app/my` | my_apps | MyAppListPage | 登录 |
| `/app/generate/:id` | app_generate | AppGeneratorPage | 登录 |
| `/app/edit/:id` | app_edit | AppEditPage | 登录 |
| `/admin/userManage` | admin_user | UserManagePage | 管理员 |
| `/admin/appManage` | admin_app | AppAdminPage（懒加载） | 管理员 |
| `/user/register` | 注册 | UserRegisterPage | - |
| `/user/login` | 登录 | UserLoginPage | - |

### 5.6 Axios 拦截器配置

```typescript
const myAxios = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,  // 从环境变量读取
  timeout: 60000,                               // 60 秒超时
  withCredentials: true,                        // Cookie 认证
})
```

- **40100（未登录）处理**：排除 `user/get/login` 和已登录页，自动跳转登录页
- **网络错误处理**：`ERR_CONNECTION_REFUSED` 显示 "后端服务未启动"

### 5.7 环境变量

| 文件 | VITE_API_BASE_URL | VITE_APP_DEPLOY_URL_PREFIX |
|------|-------------------|---------------------------|
| `.env.development` | `/api`（走 Vite 代理） | `/api/static` |
| `.env.production` | `https://your-api-domain.com/api` | `https://your-api-domain.com/api/static` |

---

## 六、项目演进历史

| 阶段 | 核心成果 | 状态 |
|------|----------|------|
| Phase 7 | Vue 工程项目生成（工具调用 + 流式消息 + 自动构建） | 已完成 |
| Phase 8 | AI 智能路由 + 封面图生成(Selenium+COS) + 源码下载 | 已完成 |
| Phase 9 | 可视化修改（iframe 选区 + 增量工具 + 创建/修改分流） | 已完成 |
| Phase 10 | AI 工作流（LangGraph4j + 图片收集 + 质量检查） | 计划中 |
| Phase 11 | 系统优化（多模型 + Redis 缓存 + 限流 + Guardrails） | 计划中 |

### Phase 7 关键成果

- `vue_project` 模式从创建应用到部署访问全链路闭环
- AI 通过 `writeFile` 工具逐文件写入，统一 JSON 流消息协议
- `AiCodeGenServiceFactory` 按 `appId + codeGenType` 隔离服务和记忆
- 自动构建（npm install + npm run build），预览/部署基于 `dist`

### Phase 8 关键成果

- AI 路由：声明式接口，优先级 "显式指定 > AI 路由 > 默认兜底"
- 封面图：Selenium 截图 + 图片压缩 + COS 上传 + 异步回写
- 源码下载：自动排除 `node_modules`/`dist`/`.env` 等
- Controller 瘦身：创建应用逻辑收敛到 `AppServiceImpl#createApp()`

### Phase 9 关键成果

- 前端可视化选区：`visualEditor.ts` 管理编辑模式、脚本注入、postMessage 通信
- 提示词增强：选中元素信息自动拼接到用户消息
- 创建/修改分流：新增修改专用 Service 接口和 Prompt
- Vue 工程工具化：新增 `readDir`/`readFile`/`modifyFile`/`deleteFile`

---

## 七、已知问题与改进建议

| 问题 | 严重度 | 说明 |
|------|--------|------|
| 重复路由守卫 | 中 | `access.ts` 和 `router_access.ts` 逻辑重复，beforeEach 执行两次 |
| counter.ts 残留 | 低 | `stores/counter.ts` 是脚手架示例，未在业务中使用 |
| Ant Design Vue 全量引入 | 中 | `app.use(Antd)` 全量注册，生产环境应按需引入减小包体积 |
| GlobalFooter 未使用 | 低 | BasicLayout 未引入 GlobalFooter 组件 |
| GlobalHeader 提前 fetch | 低 | setup 阶段直接调用 fetchLoginUser，已有 TODO |
| 批量删除未实现 | 低 | UserManagePage 批量删除仅显示"功能开发中" |
| Markdown 渲染简易 | 中 | 仅处理换行/加粗/行内代码，未使用成熟 Markdown 库 |
| Vue 项目构建依赖本地 npm | 高 | 构建服务需服务器安装 Node.js + npm，部署复杂 |
| 密码 MD5 加盐硬编码 | 中 | `MD5("aicodefree" + password)`，盐值硬编码且 MD5 不够安全 |
| CORS 允许所有域名 | 高 | `CorsConfig` 允许所有 origin，生产环境应限制 |

---

## 八、代码量统计

| 部分 | 文件数 | 核心文件行数 |
|------|--------|-------------|
| 后端 Java | 108 | AppServiceImpl(698), AiCodeGeneratorFacade(~300) |
| 前端 Vue/TS | 33 | AppGeneratorPage(1354), visualEditor.ts(435) |
| SQL | 1 | create_table.sql |
| 文档 | 10+ | Phase 7-11 计划 + 实施总结 + API 文档 |
| Prompt | 8 | AI 系统提示词模板 |

---

## 九、架构总览图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 + Vite)                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ HomePage │  │ AppGenerator │  │ AdminPages (管理后台)    │ │
│  └──────────┘  │   Page       │  └────────────────────────┘ │
│                │ ┌──────────┐ │                              │
│                │ │ 对话区    │ │                              │
│                │ │ SSE流式   │ │                              │
│                │ ├──────────┤ │                              │
│                │ │ 预览区    │ │                              │
│                │ │ iframe   │ │                              │
│                │ │ 可视化编辑│ │                              │
│                │ └──────────┘ │                              │
│                └──────────────┘                              │
└─────────────────────────┬───────────────────────────────────┘
                          │ Axios / EventSource (SSE)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   后端 (Spring Boot 3.5.5)                    │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │ Controller   │  │              Core 层                  │ │
│  │ App/User     │→│  ┌──────────────────────────────┐    │ │
│  └──────────────┘  │  │ AiCodeGeneratorFacade       │    │ │
│                    │  │  ├─ AiCodeGenServiceFactory  │    │ │
│                    │  │  ├─ StreamHandlerExecutor    │    │ │
│                    │  │  ├─ CodeFileSaverExecutor    │    │ │
│                    │  │  └─ VueProjectBuildService   │    │ │
│                    │  └──────────────────────────────┘    │ │
│                    └──────────────────────────────────────┘ │
│                          │                                   │
│              ┌───────────┼───────────┐                      │
│              ▼           ▼           ▼                      │
│  ┌──────────────┐ ┌──────────┐ ┌──────────┐                │
│  │ LangChain4j  │ │ MyBatis  │ │ Storage  │                │
│  │ AI Service   │ │ Flex ORM │ │ Strategy │                │
│  │ + 5 Tools    │ │ 4 Tables │ │ COS/Local│                │
│  └──────────────┘ └──────────┘ └──────────┘                │
│         │              │                                     │
│         ▼              ▼                                     │
│  ┌──────────────┐ ┌──────────┐                              │
│  │ DeepSeek API │ │  MySQL   │                              │
│  └──────────────┘ └──────────┘                              │
└─────────────────────────────────────────────────────────────┘
```
