# 第八阶段：功能扩展与平台能力补全 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在第七阶段已经具备多种代码生成模式与部署能力的基础上，补齐平台级能力，包括自动生成应用封面图、下载应用源码 ZIP 包，以及在创建应用时通过 AI 智能选择最合适的代码生成方案，让平台从“能生成代码”升级为“具备作品管理、分发和智能路由能力的完整应用工坊”。

**Architecture:** 第八阶段分为三条能力链路。第一条是“部署完成后异步截图并上传封面图”的视觉资产链路，核心是 Selenium 截图、图片压缩、COS 上传、异步回写 `app.cover`。第二条是“源码目录按规则过滤后打 ZIP 包下载”的交付链路，核心是项目根目录定位、文件过滤、HTTP 二进制响应和前端 Blob 下载。第三条是“根据用户提示词自动选择生成模式”的 AI 路由链路，核心是轻量级路由模型、结构化枚举输出、创建应用服务编排，以及前端对生成类型的可视化展示。

**Tech Stack:** Spring Boot 3.5.5, Java 21, Selenium 4.33.x, WebDriverManager 6.1.x, Tencent COS SDK 5.6.227, Hutool ZipUtil, LangChain4j, Reactor, Virtual Threads, Vue 3, Ant Design Vue, Vite。

---

## 1. 阶段定位

第七阶段解决的是“把代码生成出来并跑起来”。第八阶段解决的是“让生成出来的应用真正像平台作品一样被展示、下载、管理和自动分流”。

从产品视角看，第八阶段补的是 3 个非常关键的平台级能力：

- 作品封面图：让应用列表不再是一堆默认占位图。
- 源码下载：让平台不仅能在线预览，还能把完整源码交给用户带走二次开发。
- 智能路由：让用户不必理解 `single_file`、`multi_file`、`vue_project` 的技术差异，平台自动做最佳选择。

这 3 项能力看起来分散，实际上彼此是联动的：

- 只有应用成功部署，才能稳定生成真实封面图。
- 只有统一了项目输出目录规则，源码下载才能准确打包。
- 只有在应用创建时就把生成模式选对，后续部署、封面图、下载体验才会顺畅。

所以第八阶段不是“多加三个功能按钮”，而是对应用生命周期进行补全：

1. 创建应用时自动选方案。
2. 生成并部署后自动补齐封面。
3. 用户随时可以把源码打包下载。

## 2. 当前仓库基线与差距

在写第八阶段计划之前，先明确当前仓库已经具备什么、还缺什么。

### 2.1 当前已经存在的基础

后端已有：

- `App` 实体中已经存在 `cover`、`codeGenType`、`deployKey` 字段。
- `AppVO` 已经把这些字段透出给前端。
- `AppServiceImpl#deployApp()` 已经具备部署目录复制和 `deployKey` 更新能力。
- `AppConstant` 已经定义了：
  - `CODE_OUTPUT_ROOT_DIR`
  - `CODE_DEPLOY_ROOT_DIR`
  - `CODE_DEPLOY_HOST`
- `WebMvcConfig` 已经把本地目录映射到 `/static/**`。

前端已有：

- `AppCard.vue` 已经优先展示 `app.cover`，没有封面时显示默认图。
- `AppEditModal.vue` 已经能展示 `codeGenType` 和 `deployKey`。
- `AppGeneratorPage.vue` 已经具备对话、部署、预览能力。
- 首页 `HomePage.vue` 已经通过 `addApp({ initPrompt })` 创建应用。

### 2.2 当前缺失的能力

后端缺失：

- 没有封面图截图服务。
- 没有 COS 客户端配置与文件上传管理器。
- 没有截图异步触发机制。
- 没有源码下载服务和下载接口。
- 没有 AI 路由服务来自动判断 `codeGenType`。
- `AppController#addApp()` 仍然在控制层直接拼对象保存，没有抽成统一创建服务。
- `AppAddRequest` 目前只有 `initPrompt`，没有可选覆盖的 `codeGenType`。

前端缺失：

- 没有“下载代码”按钮和下载逻辑。
- 没有对“AI 自动选择了什么生成方案”的清晰展示。
- 部署成功后没有配套封面图状态反馈。

### 2.3 当前仓库里最关键的结构性差距

第八阶段里最需要注意的一点是：当前仓库有些地方已经“接近可用”，但还没真正进入平台化状态。

比如：

- `AppCard` 已经能显示 `cover`，但后台没有生成封面图的服务。
- `AppEditModal` 已经有 `codeGenType` 字段，但应用创建时并没有智能路由逻辑。
- `AppGeneratorPage` 已经有部署按钮，但部署完成后不会自动补图，也没有下载源码。

换句话说，第八阶段不是从零造轮子，而是把已有字段、已有页面、已有部署流程真正串成可用闭环。

## 3. 第八阶段目标拆解

第八阶段主目标拆成三块，每块都要以“平台级功能”标准设计，而不是只求 demo 跑通。

### 3.1 生成应用封面图

目标：应用部署完成后，自动访问真实应用页面，生成截图，压缩后上传到对象存储，并把可访问 URL 写回 `app.cover`。

### 3.2 下载应用源码

目标：用户可以下载自己应用的源码 ZIP 包，下载的是原始生成目录而不是部署目录，并自动过滤掉不应该进入压缩包的目录和文件。

### 3.3 AI 智能选择方案

目标：创建应用时，平台根据用户输入的需求自动判断使用 `SINGLE_FILE`、`MULTI_FILE` 还是 `VUE_PROJECT`，并把最终选择结果展示给用户。

## 4. 功能一：自动生成应用封面图

## 4.1 需求分析

如果应用列表只有默认图，平台会显得很像半成品。尤其这个项目本身的定位是“AI 生成应用平台”，用户在浏览应用时最先看到的不是代码质量，而是卡片封面。

封面图必须满足几个要求：

- 必须是真实页面效果，不是随机素材图。
- 必须自动生成，不能靠管理员手工上传。
- 必须压缩，不能直接用原始截图。
- 必须稳定可访问，不能只存在本地临时目录。
- 不能阻塞部署主流程。

这决定了第八阶段的封面图方案不能是“随便截个图保存到磁盘”，而必须是：

- 基于真实访问 URL 截图。
- 异步执行。
- 上传到对象存储。
- 生成失败也不能影响应用部署成功。

## 4.2 技术方案对比

图片中对网页截图方案做了对比，核心候选是：

- Selenium
- Playwright
- HtmlUnit
- Puppeteer + Node.js
- 云截图 API

### 方案 A：HtmlUnit

优点：

- 依赖轻。
- 启动快。
- 资源占用低。

缺点：

- 对现代前端页面支持很弱。
- JS 执行和 Vue/React 页面还原度差。
- 很容易出现“截图成功但页面没真正渲染完整”。

结论：不选。对现代前端项目是致命短板。

### 方案 B：Playwright

优点：

- 对现代网页支持很好。
- 性能和稳定性都不错。
- 自动化生态成熟。

缺点：

- Java 生态集成不如 Selenium 自然。
- 浏览器资源准备和运行环境管理会更重。
- 团队当前主技术栈不是 Node.js 自动化链路。

结论：理论上很好，但和当前 Java 后端栈不如 Selenium 顺手。

### 方案 C：Puppeteer + Node.js

优点：

- 截图效果成熟。
- Node 生态资料多。

缺点：

- 需要额外引入 Node 服务或脚本运行环境。
- 平台后端主栈是 Java，会带来跨语言维护成本。
- 部署与运维更复杂。

结论：不作为第八阶段首选。

### 方案 D：云截图 API

优点：

- 不需要本地浏览器驱动。
- 理论上接入快。

缺点：

- 受第三方能力、成本、配额、延迟影响。
- 调试困难。
- 可控性差。

结论：不适合作为平台基础能力首选。

### 方案 E：Selenium + WebDriverManager

优点：

- 与当前 Java 后端栈天然贴合。
- Selenium 成熟、资料多、生态稳。
- WebDriverManager 可以自动管理驱动版本。
- 对真实浏览器渲染支持好，适合 Vue 页面截图。

缺点：

- 浏览器驱动与 Headless 配置较多。
- 资源占用不算轻。
- 并发设计要小心，不能粗暴共享一个 driver。

结论：第八阶段选择 `Selenium + WebDriverManager`。

## 4.3 最终技术决策

封面图生成采用下面这组决策：

- 截图引擎使用 `Selenium + ChromeDriver + WebDriverManager`。
- 截图只针对“部署后的可访问 URL”，不针对本地预览 iframe 地址。
- 图片先保存到本地临时目录，再压缩，再上传到 COS。
- 最终只把 COS URL 写回 `app.cover`。
- 整个截图流程异步触发，不阻塞部署接口响应。
- 临时文件必须在上传后清理。
- 本地截图失败或 COS 上传失败，只记录日志与失败信息，不回滚部署。

## 4.4 为什么截图时必须使用部署后的 URL

这里必须写清楚：截图应该访问的是用户真正可访问的应用地址，例如：

```text
http://localhost/{deployKey}/
```

而不是：

- 生成目录的本地文件路径
- 前端 iframe 嵌入地址
- `/api/static/...` 的源码目录地址

原因：

- 部署后的 URL 才代表用户真实访问效果。
- 封面图应该反映“用户作品最终呈现结果”，而不是调试视图。
- 通过部署 URL 截图，可以避开很多本地相对路径与资源映射差异。

## 4.5 封面图完整链路

建议完整链路固定如下：

1. 用户点击部署。
2. 后端完成正常部署流程，生成并保存 `deployKey`。
3. 后端拼出应用 URL：`{CODE_DEPLOY_HOST}/{deployKey}/`。
4. 后端异步触发封面图任务。
5. Selenium 启动无头浏览器访问应用 URL。
6. 等待页面加载与渲染完成。
7. 本地保存截图。
8. 对截图进行压缩。
9. 上传压缩图到 COS。
10. 得到公开访问 URL。
11. 更新 `app.cover` 字段。
12. 删除本地临时截图文件。

## 4.6 依赖与配置

### 4.6.1 Maven 依赖

建议在 `pom.xml` 中新增：

```xml
<dependency>
    <groupId>org.seleniumhq.selenium</groupId>
    <artifactId>selenium-java</artifactId>
    <version>4.33.0</version>
</dependency>

<dependency>
    <groupId>io.github.bonigarcia</groupId>
    <artifactId>webdrivermanager</artifactId>
    <version>6.1.0</version>
</dependency>

<dependency>
    <groupId>com.qcloud</groupId>
    <artifactId>cos_api</artifactId>
    <version>5.6.227</version>
</dependency>
```

### 4.6.2 application.yml 配置

建议新增：

```yml
cos:
  client:
    host: https://your-cdn-or-cos-domain.com
    secretId: ${COS_SECRET_ID}
    secretKey: ${COS_SECRET_KEY}
    region: ap-shanghai
    bucket: your-bucket-name

app:
  screenshot:
    temp-dir: ${user.dir}/temp/screenshots
    width: 1600
    height: 900
    wait-after-load-millis: 2000
    compression-quality: 0.3
    upload-prefix: /screenshots
```

说明：

- `host` 应填写最终访问域名，优先填 CDN 域名或 COS 绑定域名。
- `secretId` / `secretKey` 绝不能写死到仓库。
- `compression-quality` 需要在清晰度和体积之间平衡，建议从 `0.3` 起步。

## 4.7 Selenium 配置细节

Headless Chrome 建议至少带上这些参数：

```java
options.addArguments("--headless=new")
options.addArguments("--disable-gpu")
options.addArguments("--no-sandbox")
options.addArguments("--disable-dev-shm-usage")
options.addArguments("--disable-extensions")
options.addArguments(String.format("--window-size=%d,%d", width, height))
```

说明：

- `--no-sandbox` 与 `--disable-dev-shm-usage` 对 Docker / Linux 环境很重要。
- `--window-size` 直接影响封面图宽高与首屏布局。
- `--headless=new` 比旧版 headless 模式更稳定。

## 4.8 页面加载等待策略

截图最容易踩的坑是“截图时页面还没真正渲染完”。

建议等待策略分两层：

1. 等 `document.readyState === complete`
2. 再额外 sleep 一小段时间，比如 1500~2000ms，等待异步资源和动画稳定

不要只依赖第一层，否则 Vue 应用很容易出现：

- DOM 已加载完，但接口数据还没回填
- 图片还没下载完
- 首屏骨架屏还没切换成真实内容

## 4.9 图片压缩策略

封面图不需要原图级质量，核心目标是：

- 列表页加载快
- 看起来清晰
- 存储成本低

因此建议：

- 截图后先保存原图
- 再压缩成 `.jpg`
- 最后只上传压缩图

压缩质量建议首版使用 `0.3`，后续再根据视觉效果调优。

## 4.10 COS 对象命名规则

对象 key 建议按日期分层，便于管理：

```text
/screenshots/yyyy/MM/dd/{uuid}_compressed.jpg
```

这样做有 4 个好处：

- 降低单目录对象数量压力。
- 便于按日期排查问题。
- 便于后期做生命周期管理。
- 便于 CDN 回源与缓存策略设计。

## 4.11 代码结构建议

推荐新增下面几个类：

- `config/CosClientConfig.java`
- `manager/CosManager.java`
- `utils/WebScreenshotUtils.java`
- `service/ScreenshotService.java`
- `service/impl/ScreenshotServiceImpl.java`
- `config/ScreenshotConfig.java` 或 `properties` 类

### `CosClientConfig`

职责：

- 读取 `cos.client.*` 配置
- 初始化 `COSClient`

### `CosManager`

职责：

- 执行上传对象
- 生成可访问 URL
- 做第三方交互层封装，不放业务逻辑

### `WebScreenshotUtils`

职责：

- 管理 WebDriver 初始化
- 访问 URL 截图
- 压缩图片
- 处理本地临时文件

### `ScreenshotService`

职责：

- 封装“本地截图 + 上传 COS + 删除临时文件”完整业务流程
- 对上只暴露一个返回 URL 的方法

## 4.12 异步执行策略选择

图片里提到了几种思路：

- 直接共享静态全局 `WebDriver`
- 每次请求创建新驱动
- `ThreadLocal<WebDriver>`
- 线程池 / 队列串行化
- 异步任务队列（可扩展到 MQ）

### 错误方案：多个线程共享一个静态 WebDriver

这个方案虽然简单，但不建议进入正式计划。原因：

- 并发时 driver 会互相污染。
- A 应用可能会把浏览器切到 B 应用页面。
- 问题极难排查。

### 简单方案：每次截图都新建 driver

优点：隔离干净。

缺点：

- 浏览器启动成本高。
- 频繁创建销毁资源开销大。

### 推荐方案：异步触发 + 串行截图执行器

第八阶段推荐这样定：

- 部署接口使用 `Virtual Thread` 或等价轻量异步方式触发任务，不阻塞用户。
- 真实截图执行由 `ScreenshotTaskExecutor` 串行处理，保证同一时刻只有一个 Selenium 任务使用 driver。

也就是说：

- 对外是异步的。
- 对内截图执行是串行的。

这是最稳的折中方案。

如果后续流量增长，再升级到：

- 驱动池
- 独立截图 worker
- MQ 异步任务

## 4.13 为什么这里仍然推荐 Virtual Thread

图片中使用了 Java 21 的虚拟线程来异步触发截图任务，这个方向是合理的。原因：

- 当前项目已经是 Java 21。
- 截图是典型 I/O + 外部进程 / 浏览器交互型任务。
- 虚拟线程适合“很多轻量等待、少量实际 CPU 计算”的场景。

但要强调：

- Virtual Thread 适合触发与调度。
- 不代表 Selenium driver 可以在任意虚拟线程上并发共享。

这两点必须分开理解。

## 4.14 截图失败处理策略

建议失败策略如下：

- 部署成功与截图成功解耦。
- 截图失败时：
  - 不抛出到部署接口前端。
  - 只记录错误日志。
  - `app.cover` 保持旧值或为空。
- 支持后续手动重试或定时重试。

第八阶段 MVP 不建议上复杂重试表，但至少要有清晰日志。

## 4.15 前端配合策略

其实封面图功能前端改动不大，因为：

- `AppCard.vue` 已经优先显示 `app.cover`
- 没封面时会展示默认图

真正需要考虑的是“部署后何时能看到封面更新”。

建议：

- 部署成功后前端刷新应用信息。
- 如果封面图是异步生成，允许首次刷新时仍看到默认图。
- 可选增加轻量轮询，在部署后 10~20 秒内每隔几秒拉一次应用详情，直到 `cover` 有值。

轮询不是第八阶段必须项，但如果不做，用户会误以为功能没生效。

## 4.16 封面图功能的注意事项

- 截图必须访问部署地址，不要访问源码目录。
- 临时文件上传成功后必须删除。
- COS URL 必须使用可外部访问域名。
- 截图文件名不要直接用原始用户输入，避免脏字符。
- Headless 环境要考虑 Linux / Docker 的兼容参数。

## 5. 功能二：下载应用源码 ZIP 包

## 5.1 需求分析

平台不能只让用户在线预览，还要让用户把自己生成的源码带走继续开发。否则它更像一个“在线展示工具”，而不是“应用生成平台”。

下载功能的核心不是“把目录压成 zip”这么简单，而是要回答几个问题：

- 下载哪个目录？
- 哪些文件应该排除？
- 谁可以下载？
- 响应头如何设置，前端才能拿到文件名？
- 前端如何处理二进制下载流？

## 5.2 下载目录选择

源码下载必须下载“原始生成目录”，而不是部署目录。

原因：

- 部署目录是发布产物，不一定包含源码结构。
- 对 Vue 工程而言，部署目录通常只有 `dist`，用户真正需要的是源码目录。
- 对 HTML / MULTI_FILE / VUE_PROJECT 三种模式，统一下载源码目录最符合用户预期。

建议目录规则：

- 应建立在阶段七已经统一输出目录命名的前提上。
- 推荐最终统一为：`{codeGenType}_{appId}`

例如：

- `single_file_123456`
- `multi_file_123456`
- `vue_project_123456`

如果阶段七尚未完成统一命名，第八阶段下载功能前必须先做目录标准化。

## 5.3 权限决策

下载源码默认只允许应用创建者本人。

原因：

- 源码属于用户私有产物。
- 已部署应用可公开访问，不代表源码应公开下载。

如果后续需要后台运维排障，可考虑管理员可下载，但第八阶段前台不开放管理员下载入口。

## 5.4 文件过滤策略

不是所有生成目录中的内容都应该被打进 ZIP。以下内容建议排除：

目录名排除：

- `node_modules`
- `.git`
- `dist`
- `build`
- `.DS_Store`
- `.env`
- `target`
- `.mvn`
- `.idea`
- `.vscode`
- `.cache`

扩展名排除：

- `.log`
- `.tmp`
- `.cache`

设计原则：

- 不通过硬编码绝对路径过滤。
- 通过路径相对片段逐层判断。
- 过滤逻辑统一放在服务层，不散落在 controller。

## 5.5 为什么要排除 `dist` 和 `node_modules`

这两个目录最容易让下载包失控：

- `node_modules` 体积巨大，而且完全可以重新安装。
- `dist` 是构建产物，不是源码。

如果不排除，用户下载包可能变成几十 MB 甚至几百 MB，完全背离“下载源码”的目的。

## 5.6 后端服务设计

建议新增：

- `service/ProjectDownloadService.java`
- `service/impl/ProjectDownloadServiceImpl.java`

对外职责：

- 接收项目根目录
- 接收下载文件名
- 向 `HttpServletResponse` 输出 ZIP 内容

内部职责：

- 校验项目目录存在
- 创建过滤器
- 设置响应头
- 调用 `ZipUtil.zip(...)`

## 5.7 为什么这里推荐 Hutool ZipUtil

当前仓库已经引入 Hutool，因此这里优先用 `ZipUtil` 而不是重新手写 `ZipOutputStream`，原因很直接：

- 减少样板代码。
- 支持文件过滤器。
- 集成成本低。

第八阶段重点不是“手写压缩算法”，而是把目录过滤和下载链路设计正确。

## 5.8 下载接口设计

建议在 `AppController` 中新增：

```text
GET /app/download/{appId}
```

接口职责：

1. 校验 `appId`
2. 查询应用
3. 校验当前用户是否为创建者
4. 根据 `codeGenType + appId` 组装源码目录
5. 调用下载服务输出 ZIP

注意：

- 这是文件下载接口，返回的是二进制流，不是 `BaseResponse<T>`。
- 因此控制器方法应直接写响应流，不要再包统一响应体。

## 5.9 HTTP 响应头要求

必须正确设置：

```http
Content-Type: application/zip
Content-Disposition: attachment; filename="app-{appId}.zip"
```

推荐文件名：

```text
app-{appId}.zip
```

不要只用裸 `appId.zip`，可读性差一些。

另外，若前端要读取 `Content-Disposition`，还要保证 CORS 已暴露该头部。

## 5.10 前端下载策略

图片里采用的是浏览器原生 `fetch + blob + a 标签下载`，这个方向是正确的。

为什么不直接复用普通 Axios 返回 JSON 的逻辑：

- 下载接口返回的是二进制流，不是普通 JSON。
- 统一 request 封装里通常会做 JSON 拦截和错误处理，不适合直接套。
- `fetch` 在处理 `blob` 与原始响应头时更直接。

推荐前端流程：

1. 点击“下载代码”按钮。
2. `fetch('/app/download/{appId}')`
3. 读取 `Content-Disposition` 获取文件名。
4. `response.blob()` 转成 Blob。
5. `URL.createObjectURL(blob)` 生成下载链接。
6. 通过临时 `<a>` 标签触发下载。
7. 调用 `URL.revokeObjectURL(...)` 释放内存。

## 5.11 前端交互建议

建议在 `AppGeneratorPage.vue` 顶部操作区增加：

- `应用详情`
- `下载代码`
- `部署`

当前页面已经有部署按钮，所以下载按钮加在同一组里最自然。

按钮状态建议：

- 未登录：不显示或禁用。
- 非应用本人：禁用。
- 正在下载：显示 loading。

## 5.12 下载功能的注意事项

- 下载的是源码目录，不是部署目录。
- ZIP 响应不能走统一 `BaseResponse`。
- 过滤逻辑必须在服务端做，不能指望前端忽略敏感文件。
- `.env`、`node_modules`、`dist` 必须排除。
- 若未来支持模板项目，还要排除模板缓存目录。

## 5.13 可选增强项

图片中提到两个不错的扩展方向，可以写入文档但不纳入第八阶段必须项：

- 记录下载次数，用于热门作品分析。
- 仅当应用已成功部署时才允许下载。

这两个都合理，但不是第八阶段主链路必须项。

## 6. 功能三：AI 智能选择代码生成方案

## 6.1 需求分析

平台目前至少会存在三种生成模式：

- `SINGLE_FILE`
- `MULTI_FILE`
- `VUE_PROJECT`

如果让用户自己选，会有两个问题：

- 用户未必理解三种模式的技术区别。
- 用户选错之后，后续生成、部署、下载体验都会变差。

所以更好的方案是：

- 用户只描述需求。
- 平台自动判断用哪种生成模式。

这本质上是一个“创建前的轻量分类任务”，不需要推理型大模型全力输出长内容，只需要一个快且便宜的分类器。

## 6.2 为什么这个场景适合 AI 路由而不是硬编码规则

当然可以手写规则，比如：

- 包含“后台”“管理系统” -> `VUE_PROJECT`
- 包含“官网” -> `MULTI_FILE`
- 包含“简历” -> `SINGLE_FILE`

但这种规则很快就会失控：

- 用户表达方式很多样。
- 需求复杂度不只是关键词能判断。
- 手写规则容易和真实需求错位。

因此第八阶段应选择“轻量 AI 路由”为主，关键词规则只作为兜底或 override。

## 6.3 技术方案对比

### 方案 A：纯关键词规则

优点：

- 快。
- 不花 token。

缺点：

- 维护困难。
- 精度差。
- 面对复杂描述很容易误判。

### 方案 B：关键词规则 + AI 兜底

优点：

- 可解释性更强。
- 成本可控。

缺点：

- 两套规则并存，维护复杂。
- 会出现“规则说 A，AI 说 B”的冲突。

### 方案 C：AI 结构化输出枚举

优点：

- 简洁。
- 容易扩展。
- 适合 LangChain4j 的结构化输出能力。

缺点：

- 需要写好提示词。
- 需要小心模型配置，尤其是 DeepSeek 的 JSON 模式限制。

结论：第八阶段采用 `AI 结构化输出枚举`。

## 6.4 重要命名决策：不要引入第二套枚举语义

图片里的示例会把简单页面类型写成 `HTML`。但当前仓库现有枚举是：

- `SINGLE_FILE`
- `MULTI_FILE`

因此第八阶段必须统一使用当前仓库语义，不要新增 `HTML` 这套第二命名，否则会造成：

- 提示词写 `HTML`
- Java 枚举写 `SINGLE_FILE`
- 前端文案又叫“单文件模式”

最终全链路非常混乱。

所以本仓库第八阶段 AI 路由输出应该统一为：

- `SINGLE_FILE`
- `MULTI_FILE`
- `VUE_PROJECT`

## 6.5 最终路由决策

第八阶段采用下面这组决策：

- 路由模型使用轻量级普通 `chatModel`，不使用推理流模型。
- 路由结果直接返回 `CodeGenTypeEnum`。
- 默认走 AI 路由。
- 如果前端或后台显式传入 `codeGenType`，则显式值优先，跳过 AI 路由。

这条“显式优先，AI 兜底”的决策很重要，因为它能兼容：

- 首页普通用户极简输入
- 后台管理员手工指定模式
- 调试场景强制选择模式

## 6.6 路由规则定义

建议路由规则写得非常清晰：

- `SINGLE_FILE`
  - 适合单页、简单展示、个人简介、邀请函、公告页、单 HTML 落地页
  - 不需要复杂路由、复杂状态、复杂交互

- `MULTI_FILE`
  - 适合静态多模块网站、官网、企业站、营销展示页、纯 HTML/CSS/JS 拆分项目
  - 有多个区块或若干页面，但仍不需要完整前端工程能力

- `VUE_PROJECT`
  - 适合后台、管理系统、复杂交互、表单流程、数据展示、可扩展项目、需要组件化和路由的应用

## 6.7 路由提示词资源文件

建议新增：

- `src/main/resources/prompt/codegen-routing-system-prompt.txt`

下面这份提示词可直接作为第八阶段文档里的基准版本：

```text
你是一个代码生成方案路由助手。你的任务不是生成代码，而是根据用户的需求描述，从以下三个生成类型中严格选择一个最合适的结果：

可选结果只有：
- SINGLE_FILE
- MULTI_FILE
- VUE_PROJECT

类型含义：
1. SINGLE_FILE
   - 适合简单单页展示页面
   - 只有一个 HTML 文件，样式和脚本都可以内联
   - 典型场景：个人介绍、简历、活动落地页、简单宣传页、邀请函、公告页

2. MULTI_FILE
   - 适合静态多模块网站或纯前端拆分页面
   - 主要由 HTML、CSS、JS 文件组成
   - 典型场景：企业官网、产品介绍站、营销页、静态多页面站点

3. VUE_PROJECT
   - 适合复杂交互型前端应用
   - 需要组件化、路由、状态管理思维或后续扩展能力
   - 典型场景：管理后台、数据面板、在线工具、复杂作品展示站、需要长期迭代的前端项目

判断规则：
- 如果需求明显只是一个简单单页，选择 SINGLE_FILE。
- 如果需求包含多个区块、多个静态页面或更适合 HTML/CSS/JS 拆分维护，选择 MULTI_FILE。
- 如果需求涉及后台、管理系统、复杂交互、表单、数据展示、组件化、路由或未来扩展，选择 VUE_PROJECT。
- 如果用户明确提到“Vue”“后台”“管理系统”“复杂交互”“作品集网站并希望后续扩展”等倾向，优先选择 VUE_PROJECT。

输出要求：
- 只能返回一个结果。
- 不要解释原因。
- 不要输出多余文本。
- 不要输出 Markdown。
- 不要输出 JSON。
- 输出必须严格是 SINGLE_FILE、MULTI_FILE、VUE_PROJECT 三者之一。
```

## 6.8 为什么这里明确要求“不要输出 JSON”

图片里提到一个非常容易踩的坑：如果对 DeepSeek 的 `chat-model` 开启 `response-format: json_object` 或 `strict-json-schema`，模型可能会要求 prompt 中必须出现 `json` 相关措辞，否则直接报错。

而这个场景返回的是一个简单枚举，不是复杂 JSON 对象，所以第八阶段建议：

- 路由服务不要强开 `response-format: json_object`
- 不要强开 `strict-json-schema`

让 LangChain4j 直接把模型输出映射到 `CodeGenTypeEnum` 即可。

这是第八阶段非常关键的配置决策。

## 6.9 路由服务设计

建议新增：

- `ai/AiCodeGenTypeRoutingService.java`
- `ai/AiCodeGenTypeRoutingServiceFactory.java`

接口形式建议：

```java
public interface AiCodeGenTypeRoutingService {

    @SystemMessage(fromResource = "prompt/codegen-routing-system-prompt.txt")
    CodeGenTypeEnum routeCodeGenType(String userPrompt);
}
```

Factory 建议使用现有注入的普通 `ChatModel`，不要使用推理流模型。

## 6.10 应用创建流程改造

这是第八阶段最重要的业务编排改造点。

当前仓库里，`AppController#addApp()` 仍然在控制层内直接：

- 校验 prompt
- new `App()`
- 直接 `save(app)`

这不利于挂接 AI 路由，也不利于后续扩展。

第八阶段建议改造成：

1. `AppController#addApp()` 只保留参数校验和用户获取。
2. 新增 `AppService#createApp(AppAddRequest, User)`。
3. 在 `AppServiceImpl#createApp()` 中：
   - 读取 `initPrompt`
   - 如果 `request.codeGenType` 显式传值，优先使用它
   - 否则调用 `AiCodeGenTypeRoutingService.routeCodeGenType(initPrompt)`
   - 生成应用名
   - 保存应用

这样控制层更干净，业务逻辑更集中。

## 6.11 `AppAddRequest` 的最终设计建议

虽然当前 `AppAddRequest` 只有 `initPrompt`，但为了兼容阶段七和第八阶段的演进，建议把它改成：

```java
private String initPrompt;
private String codeGenType;
```

其中：

- 普通首页创建应用时，可以不传 `codeGenType`
- 后端自动路由
- 管理员 / 调试界面可以显式传入 `codeGenType`

这样可以同时兼容“自动路由”和“人工指定”。

## 6.12 前端展示策略

智能路由如果只在后端发生、前端完全不可见，用户会很迷惑。第八阶段建议前端明确展示生成类型。

推荐展示位置：

- `AppGeneratorPage.vue` 顶部标题右侧
- `AppEditModal.vue` 或应用详情弹层
- 应用卡片角标（可选）

显示文案要做格式化，不要直接把原始枚举值扔给用户。建议映射：

- `SINGLE_FILE` -> `单文件模式`
- `MULTI_FILE` -> `多文件模式`
- `VUE_PROJECT` -> `Vue 项目模式`

## 6.13 首页创建流程与第八阶段的关系

当前首页 `HomePage.vue` 仍然使用：

```ts
addApp({ initPrompt: searchText.value })
```

这是好的，因为它天然适合 AI 路由模式。第八阶段可以保留这个入口不动，智能选择完全在后端完成。

也就是说：

- 首页继续保持“只说需求，不选技术”
- 平台自动路由

这正是第八阶段体验升级的关键。

## 6.14 智能路由功能的注意事项

- 不要让 prompt 返回 `HTML`，要返回当前仓库实际枚举 `SINGLE_FILE`。
- 不要对这个路由服务开启强制 JSON object 响应模式。
- 显式传入的 `codeGenType` 要高于 AI 路由结果。
- 路由服务只负责分类，不参与代码生成。
- 路由失败时要有兜底策略，推荐兜底到 `MULTI_FILE` 或 `SINGLE_FILE`，但要记录日志。

## 7. 与当前仓库的集成要点

## 7.1 后端集成点

建议修改或新增的关键位置：

- `pom.xml`
- `src/main/resources/application.yml`
- `src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java`
- `src/main/java/com/adcage/acaicodefree/service/AppService.java`
- `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- `src/main/java/com/adcage/acaicodefree/constant/AppConstant.java`

新增建议：

- `src/main/java/com/adcage/acaicodefree/config/CosClientConfig.java`
- `src/main/java/com/adcage/acaicodefree/manager/CosManager.java`
- `src/main/java/com/adcage/acaicodefree/utils/WebScreenshotUtils.java`
- `src/main/java/com/adcage/acaicodefree/service/ScreenshotService.java`
- `src/main/java/com/adcage/acaicodefree/service/impl/ScreenshotServiceImpl.java`
- `src/main/java/com/adcage/acaicodefree/service/ProjectDownloadService.java`
- `src/main/java/com/adcage/acaicodefree/service/impl/ProjectDownloadServiceImpl.java`
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingService.java`
- `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingServiceFactory.java`
- `src/main/resources/prompt/codegen-routing-system-prompt.txt`

## 7.2 前端集成点

建议修改：

- `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
- `ac-ai-code-free-fronted/src/components/AppEditModal.vue`
- `ac-ai-code-free-fronted/src/components/AppCard.vue`（可选增加类型角标）
- `ac-ai-code-free-fronted/src/api/appController.ts`
- `ac-ai-code-free-fronted/src/api/typings.d.ts`

如果采用手写下载逻辑，下载接口不一定必须走 OpenAPI 生成文件，可以单独在页面中使用 `fetch` 实现。

## 8. 第八阶段完整任务拆分

### Task 1：补齐截图、COS、下载所需依赖与配置

**Files:**

- Modify: `pom.xml`
- Modify: `src/main/resources/application.yml`

**目标：**

- 增加 Selenium、WebDriverManager、COS SDK 依赖。
- 增加 `cos.client.*` 配置。
- 增加 `app.screenshot.*` 配置。

**关键决策：**

- 截图引擎固定为 Selenium。
- 对象存储固定为 COS。

**验证：**

- 应用能正常启动。
- COSClient Bean 能正确创建。

### Task 2：实现 COS 配置层与通用上传管理器

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/config/CosClientConfig.java`
- Create: `src/main/java/com/adcage/acaicodefree/manager/CosManager.java`

**目标：**

- 初始化 COSClient。
- 实现文件上传与 URL 生成。

**关键决策：**

- `CosManager` 只做第三方交互封装，不直接写业务逻辑。

**验证：**

- 本地可上传测试文件到 COS，并拿到正确 URL。

### Task 3：实现 Selenium 截图工具与本地压缩清理能力

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/utils/WebScreenshotUtils.java`

**目标：**

- 无头浏览器访问 URL 并截图。
- 等待页面加载完成。
- 压缩图片。
- 删除临时文件。

**关键决策：**

- Headless 参数必须考虑 Docker / Linux。
- 页面等待采用“双阶段等待”。

**验证：**

- 对公开网站截图成功，输出压缩图片路径。

### Task 4：实现 ScreenshotService 并打通 COS 上传

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/service/ScreenshotService.java`
- Create: `src/main/java/com/adcage/acaicodefree/service/impl/ScreenshotServiceImpl.java`

**目标：**

- 完成“截图 -> 压缩 -> 上传 -> 清理”完整链路。

**关键决策：**

- 对上暴露返回封面 URL 的统一方法。
- 上传失败与清理失败分别记录日志。

**验证：**

- 传入部署地址后，可返回可访问的 COS 图片地址。

### Task 5：在应用部署后异步触发封面图生成

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/service/AppService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

**目标：**

- 在 `deployApp()` 成功后拼接应用 URL。
- 异步触发封面图生成。
- 成功后更新 `app.cover`。

**关键决策：**

- 部署成功与截图成功解耦。
- 异步触发，不能阻塞部署接口返回。

**验证：**

- 部署应用后 5~20 秒内，`app.cover` 被更新。

### Task 6：实现源码下载服务与控制器接口

**Files:**

- Create: `src/main/java/com/adcage/acaicodefree/service/ProjectDownloadService.java`
- Create: `src/main/java/com/adcage/acaicodefree/service/impl/ProjectDownloadServiceImpl.java`
- Modify: `src/main/java/com/adcage/acaicodefree/controller/AppController.java`

**目标：**

- 增加 `/app/download/{appId}` 下载接口。
- 设置 ZIP 响应头。
- 过滤不应进入压缩包的目录和文件。

**关键决策：**

- 下载源码目录，不下载部署目录。
- 下载接口直接写二进制流，不包 BaseResponse。

**验证：**

- 浏览器可成功下载 `app-{appId}.zip`。

### Task 7：重构应用创建流程并引入 AI 路由服务

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/AppService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- Modify: `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingService.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingServiceFactory.java`
- Create: `src/main/resources/prompt/codegen-routing-system-prompt.txt`

**目标：**

- 创建应用时自动判断生成模式。
- 支持显式传入模式覆盖 AI 路由。
- 控制层瘦身，业务逻辑进入 Service。

**关键决策：**

- 返回当前仓库真实枚举：`SINGLE_FILE` / `MULTI_FILE` / `VUE_PROJECT`。
- 路由模型使用普通 `chatModel`。

**验证：**

- 简单个人页路由到 `SINGLE_FILE`
- 企业官网路由到 `MULTI_FILE`
- 管理后台 / 复杂作品站路由到 `VUE_PROJECT`

### Task 8：补齐前端下载按钮与生成类型展示

**Files:**

- Modify: `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
- Modify: `ac-ai-code-free-fronted/src/components/AppEditModal.vue`
- Modify: `ac-ai-code-free-fronted/src/components/AppCard.vue`（可选）
- Modify: `ac-ai-code-free-fronted/src/api/typings.d.ts`

**目标：**

- 顶部操作区增加“下载代码”按钮。
- 增加生成类型标签展示。
- 支持基于 `fetch + blob` 的真实下载。

**关键决策：**

- 文件下载不强依赖 OpenAPI 自动生成方法。
- 用户展示文案使用中文标签映射。

**验证：**

- 点击“下载代码”后浏览器成功下载 ZIP 包。
- 页面中能看到正确的生成类型标签。

### Task 9：补齐测试与运维级清理任务

**Files:**

- Create: `src/test/java/.../WebScreenshotUtilsTest.java`
- Create: `src/test/java/.../ProjectDownloadServiceTest.java`
- Create: `src/test/java/.../AiCodeGenTypeRoutingServiceTest.java`
- Create/Modify: 截图清理调度配置类

**目标：**

- 覆盖截图成功路径。
- 覆盖 ZIP 文件过滤逻辑。
- 覆盖 AI 路由结果。
- 增加临时截图目录清理任务。

**关键决策：**

- 测试尽量不依赖真实浏览器和真实 COS，必要时做本地集成测试分层。

**验证：**

- `mvn test`
- 本地手工验证部署、截图、下载、路由三条主链路。

## 9. 验收标准

第八阶段完成后，至少应满足：

- 部署应用后可异步生成封面图并回写 `app.cover`。
- 应用卡片优先显示真实封面图。
- 用户可以下载自己应用的源码 ZIP 包。
- ZIP 包不会包含 `node_modules`、`dist`、`.env` 等不应下发内容。
- 创建应用时无需用户手工选择技术方案，平台会自动判断。
- AI 路由返回值与当前仓库枚举一致，不引入 `HTML` 这类第二套命名。
- 页面中可以看到生成类型展示。
- 任何截图 / 上传失败都不会影响部署主流程成功返回。

## 10. 风险与注意事项

### 10.1 截图任务会消耗浏览器资源

如果未来部署操作很多，截图任务会变成热点。第八阶段先保证正确性和稳定性，不盲目追求高并发。必要时再引入独立 worker 或消息队列。

### 10.2 对象存储配置最容易出问题

常见问题包括：

- 域名配置错误
- bucket 区域错误
- 权限策略不对
- CDN / COS 域名未开启公开访问

这些问题都要写进联调 checklist。

### 10.3 DeepSeek 路由模型配置不要乱开 JSON 选项

这个坑要反复强调：返回简单枚举时，不要强启 `response-format: json_object` 和 `strict-json-schema`。否则很容易因为 prompt 中没有明确包含 `json` 关键词而直接报错。

### 10.4 下载功能属于文件响应，不要按 JSON 接口心智处理

前端若还按普通 JSON 接口处理，会导致：

- 无法下载文件
- 响应头读取不到
- 文件名丢失

### 10.5 第七阶段与第八阶段的兼容策略要先定好

尤其是 `codeGenType`：

- 阶段七可能允许显式指定模式。
- 阶段八希望自动路由。

正确策略是：

- `显式指定 > AI 路由 > 默认兜底`

这样两阶段不会互相打架。

## 11. 给 AI 的补充提示词建议

第八阶段除了“代码生成提示词”之外，还会新增一个“路由提示词”。如果后续还希望让 AI 参与封面图状态提示或下载提示文案，建议单独维护轻量提示词，不要和代码生成 prompt 混在一起。

### 11.1 路由提示词设计原则

- 只负责分类，不生成代码。
- 输出必须唯一。
- 术语必须与仓库枚举一致。
- 不要输出解释，避免解析复杂化。

### 11.2 不推荐的路由提示词写法

下面这种写法不推荐：

```text
请帮我分析一下用户更适合什么技术方案，并用 JSON 详细说明理由。
```

原因：

- 输出变复杂。
- 容易引发 JSON 模式配置问题。
- 对这个场景完全过度设计。

### 11.3 推荐的路由提示词写法

上文给出的 `codegen-routing-system-prompt.txt` 就是推荐基线，重点就是：

- 只有三个结果
- 只能返回一个
- 不要解释
- 不要 JSON

## 12. 最后结论

如果说第七阶段解决的是“生成能力”，那第八阶段解决的就是“平台能力”。

第八阶段完成后，平台会从单纯的代码生成器进一步升级为：

- 会自动挑方案
- 会自动补作品封面
- 会把源码完整交付给用户

而这三项能力一旦补齐，平台的用户心智就会发生变化：

- 不再只是“我让 AI 生成一段网页代码”
- 而是“我在这个平台创建、展示、部署、下载、管理一个完整应用作品”

这就是第八阶段真正的价值。
