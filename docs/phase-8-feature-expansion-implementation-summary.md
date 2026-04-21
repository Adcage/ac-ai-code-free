# 第八阶段功能扩展实施总结（教学版）

## 1. 这份文档是写给谁看的？

这不是一份“流水账式变更记录”，而是一份**把这一阶段真正讲明白的教学型总结**。

如果你只是想知道“改了哪些文件”，看文件列表就够了；
但如果你想真正学会下面这些问题，这份文档才是重点：

- 为什么第八阶段一定要把“创建、部署、下载、封面”串成完整链路？
- 为什么 AI 路由不能继续写在 Controller 里？
- LangChain4j 到底是怎么把一个 Java 接口变成 AI 能力的？
- 为什么截图要异步、为什么要串行、为什么还要补状态和重试？
- 为什么下载源码不能直接把整个目录压缩完事？
- 前端为什么不能继续硬编码 `vue_project`？

我的目标不是告诉你“我做完了”，而是要让你读完之后，**知道这次为什么这样设计、代码为什么这样写、以后你自己如何继续扩展**。

---

## 2. 第八阶段到底做了什么？

第八阶段的目标，不是简单加三个按钮，而是把平台从“能生成代码”升级成“有作品生命周期的平台”。

这一阶段最终完成了 4 条主线能力：

1. **创建应用时自动选择代码生成模式**
   - 用户只输入需求，不用理解 `single_file / multi-file / vue_project` 的技术区别。
   - 后端通过 LangChain4j 调用轻量模型做“路由判断”。

2. **部署后自动异步生成封面图**
   - 后端在部署成功后拼出真实访问 URL。
   - 使用 Selenium 访问页面截图、压缩、上传 COS，最后回写 `app.cover`。
   - 后续又补了**状态可观测 + 失败重试**。

3. **下载应用源码 ZIP 包**
   - 用户可以下载自己应用的源码，而不是部署产物。
   - 自动排除 `node_modules`、`dist`、`.env` 等不应该发给用户的内容。

4. **前端完整展示平台状态**
   - 首页不再硬编码生成模式。
   - 详情页展示生成模式、封面生成状态、下载权限状态。
   - 作品卡片也明确告诉用户：谁可以下载源码。

从业务视角看，这 4 条线实际上补全的是同一个生命周期：

```text
用户描述需求
  -> 平台自动路由生成方案
  -> AI 生成代码
  -> 用户部署应用
  -> 平台自动补作品封面
  -> 用户下载源码继续开发
```

这就是为什么第八阶段不是“散点功能”，而是“平台化能力补全”。

---

## 3. 这次修改的关键文件一览

### 3.1 后端新增/修改

- 新增 `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingService.java`
- 新增 `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingServiceFactory.java`
- 新增 `src/main/resources/prompt/codegen-routing-system-prompt.txt`
- 修改 `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- 修改 `src/main/java/com/adcage/acaicodefree/service/AppService.java`
- 修改 `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- 新增 `src/main/java/com/adcage/acaicodefree/config/CosClientConfig.java`
- 新增 `src/main/java/com/adcage/acaicodefree/config/properties/CosClientProperties.java`
- 新增 `src/main/java/com/adcage/acaicodefree/config/properties/ScreenshotProperties.java`
- 新增 `src/main/java/com/adcage/acaicodefree/manager/CosManager.java`
- 新增 `src/main/java/com/adcage/acaicodefree/utils/WebScreenshotUtils.java`
- 新增 `src/main/java/com/adcage/acaicodefree/service/ScreenshotService.java`
- 新增 `src/main/java/com/adcage/acaicodefree/service/impl/ScreenshotServiceImpl.java`
- 新增 `src/main/java/com/adcage/acaicodefree/service/ProjectDownloadService.java`
- 新增 `src/main/java/com/adcage/acaicodefree/service/impl/ProjectDownloadServiceImpl.java`
- 修改 `src/main/java/com/adcage/acaicodefree/model/vo/app/AppVO.java`
- 修改 `src/main/resources/application.yml`
- 修改 `pom.xml`

### 3.2 前端新增/修改

- 修改 `ac-ai-code-free-fronted/src/pages/HomePage.vue`
- 修改 `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
- 修改 `ac-ai-code-free-fronted/src/components/AppEditModal.vue`
- 修改 `ac-ai-code-free-fronted/src/components/AppCard.vue`
- 修改 `ac-ai-code-free-fronted/src/api/typings.d.ts`

### 3.3 测试新增/修改

- 新增 `src/test/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingServiceTest.java`
- 新增 `src/test/java/com/adcage/acaicodefree/service/impl/ProjectDownloadServiceImplTest.java`
- 新增 `src/test/java/com/adcage/acaicodefree/service/impl/ScreenshotServiceImplTest.java`
- 新增 `src/test/java/com/adcage/acaicodefree/service/impl/AppServiceCoverTaskStateTest.java`
- 修改 `src/test/java/com/adcage/acaicodefree/controller/AppControllerTest.java`
- 修改 `src/test/java/com/adcage/acaicodefree/controller/AppChatE2ETest.java`
- 修改 `ac-ai-code-free-fronted/tests/chat-flow.e2e.test.mjs`

---

## 4. 最重要的架构变化：创建应用从 Controller 迁到 Service

这是本阶段最关键的重构之一。

### 4.1 为什么必须改？

原来的 `AppController#addApp()` 是“控制层直接 new 实体 + save”的写法。这样写有一个明显问题：

- Controller 本该负责“接收参数、做基础校验、调用服务”；
- 但它却承担了“生成模式决定、应用名生成、入库逻辑”等业务职责。

一旦你想加 AI 路由，这种写法就会变得非常难维护。

因为“创建应用”已经不再只是一次简单插入，而是变成了：

```text
校验 prompt
-> 判断是否显式指定 codeGenType
-> 如果没有则让 AI 路由
-> 把枚举结果映射成真实存储值
-> 生成应用名
-> 保存应用
```

这已经是**业务编排**了，不应该继续留在 Controller。

### 4.2 重构后的 Controller

`src/main/java/com/adcage/acaicodefree/controller/AppController.java`

```java
@PostMapping("/add")
public BaseResponse<Long> addApp(@RequestBody AppAddRequest appAddRequest, HttpServletRequest request) {
    ThrowUtils.throwIf(appAddRequest == null, ErrorCode.PARAMS_ERROR);
    ThrowUtils.throwIf(StrUtil.isBlank(appAddRequest.getInitPrompt()), ErrorCode.PARAMS_ERROR, "初始化 prompt 不能为空");
    User loginUser = userService.getLoginUser(request);
    Long appId = appService.createApp(appAddRequest, loginUser);
    return ResultUtils.success(appId);
}
```

### 4.3 你要学会的点

这里的重构思想非常重要：

- Controller 只做**入参校验 + 登录用户获取 + 调服务**；
- 所有“如何创建应用”的规则，都收敛到 `AppServiceImpl#createApp()`；
- 后续如果你要增加：
  - 应用初始化默认封面
  - 默认标签
  - 创建审计日志
  - 模板来源记录
  都可以继续加在 Service，而不用把 Controller 搞成一锅粥。

这就是典型的“**控制层瘦身，服务层收口业务**”。

---

## 5. LangChain4j 是怎么接入 AI 路由的？这部分要真正看懂

这一节我会详细讲，因为这是这次实现里最值得你学的部分。

很多人第一次用 LangChain4j，只会把它当成“Java 调大模型的 SDK”。
但在这个项目里，我们用的不是最原始的 HTTP 调用方式，而是它更高级的能力：

- **声明式 AI Service**
- **Prompt 资源化**
- **模型实例工厂化**
- **流式输出 / 工具调用 / 记忆隔离**

你要把它理解成：

> “我不是在手动拼请求体，而是在用 Java 接口描述一个 AI 能力，LangChain4j 帮我把这个接口变成真正可调用的大模型服务。”

这和手写 `RestTemplate` / `OkHttp` 有本质差别。

---

## 6. 先看项目里原本就有的 LangChain4j 用法

### 6.1 声明式 AI 接口

`src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`

```java
public interface AiCodeGeneratorService {

    @SystemMessage(fromResource = "prompt/codegen-single-file-system-prompt.txt")
    SingleCodeResult generateSingleFileCode(String userMessage);

    @SystemMessage(fromResource = "prompt/codegen-multi-file-system-prompt.txt")
    MultiFileCodeResult generateMultiFileCode(String userMessage);

    @SystemMessage(fromResource = "prompt/codegen-vue-project-system-prompt.txt")
    TokenStream generateVueProjectCodeStream(@MemoryId Long appId, @UserMessage String userMessage);
}
```

### 6.2 这一段到底是什么意思？

#### 第一层：`@SystemMessage(fromResource = "...")`

它告诉 LangChain4j：

- 不要把系统提示词写在 Java 字符串里；
- 去 `resources/prompt/...` 文件里读取系统提示词；
- 用这个提示词作为该方法的“系统角色输入”。

这有三个巨大好处：

1. **提示词独立管理**：修改 prompt 不需要改 Java 代码。
2. **便于版本迭代**：后续 A/B prompt 很方便。
3. **阅读成本更低**：Java 代码只看接口含义，prompt 细节留给资源文件。

#### 第二层：方法签名就是 AI 能力定义

例如：

```java
SingleCodeResult generateSingleFileCode(String userMessage);
```

它表达的是：

- 输入：用户一句话需求；
- 输出：一个结构化对象 `SingleCodeResult`；
- 大模型被要求把结果组织成这个 Java 类型可映射的格式。

也就是说，你不是拿到一大串字符串后自己拆，而是让 LangChain4j帮你做“**模型输出 -> Java 类型**”映射。

#### 第三层：`@MemoryId`

```java
TokenStream generateVueProjectCodeStream(@MemoryId Long appId, @UserMessage String userMessage);
```

这行非常关键。

它的意思是：

- `appId` 不是普通业务参数；
- 它是这个 AI 会话的“记忆隔离标识”；
- LangChain4j 会把同一个 `MemoryId` 的历史上下文关联起来。

所以这里不是“随便传个 Long”，而是：

> 同一个应用的多轮 Vue 工程生成，会共享上下文；不同应用之间则天然隔离。

这比你自己维护 `Map<Long, List<Message>>` 更优雅，也更符合框架设计。

---

## 7. 再看项目里原本的工厂：为什么它是理解本次 AI 路由的前提

`src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`

```java
protected AiCodeGeneratorService createLegacyService() {
    return AiServices.builder(AiCodeGeneratorService.class)
            .chatLanguageModel(chatModel)
            .streamingChatLanguageModel(legacyStreamingChatLanguageModel)
            .build();
}

protected AiCodeGeneratorService createVueProjectService(Long appId) {
    return AiServices.builder(AiCodeGeneratorService.class)
            .chatLanguageModel(chatModel)
            .streamingChatLanguageModel(reasoningStreamingChatModel)
            .tools(fileWriteTool)
            .chatMemoryProvider(memoryId -> resolveChatMemory(memoryId, appId))
            .build();
}
```

### 7.1 这段代码说明了什么？

这是 LangChain4j 的核心入口：

```java
AiServices.builder(AiCodeGeneratorService.class)
```

它会做一件事：

> 按照 `AiCodeGeneratorService` 这个接口的注解、参数和返回值，动态创建一个真正可调用的大模型代理对象。

你可以把它想象成：

- Spring 的 `FeignClient` 是“把 Java 接口变成 HTTP 客户端”；
- LangChain4j 的 `AiServices.builder(...)` 是“把 Java 接口变成 AI 客户端”。

### 7.2 为什么 Vue 模式要单独工厂化？

因为 Vue 项目模式比单文件、多文件复杂很多：

- 它需要流式输出；
- 它需要工具调用（这里是 `FileWriteTool`）；
- 它需要 ChatMemory；
- 它可能需要更强的模型。

所以工厂不是“写着好看”，而是在表达一个重要架构决策：

> 不同 AI 能力，应该按能力类型装配不同模型与上下文，而不是所有场景共用一套参数。

这一点也直接启发了本次 AI 路由服务的设计。

---

## 8. 本次新增的 LangChain4j 路由服务：最小而正确

### 8.1 新增接口

`src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingService.java`

```java
public interface AiCodeGenTypeRoutingService {

    @SystemMessage(fromResource = "prompt/codegen-routing-system-prompt.txt")
    CodeGenTypeEnum routeCodeGenType(String userPrompt);
}
```

### 8.2 新增工厂

`src/main/java/com/adcage/acaicodefree/ai/AiCodeGenTypeRoutingServiceFactory.java`

```java
@Component
public class AiCodeGenTypeRoutingServiceFactory {

    @Resource
    private ChatLanguageModel chatModel;

    public AiCodeGenTypeRoutingService createService() {
        return AiServices.builder(AiCodeGenTypeRoutingService.class)
                .chatLanguageModel(chatModel)
                .build();
    }
}
```

### 8.3 这段设计为什么很漂亮？

因为它做到了三个“恰到好处”：

#### 第一，接口极简

就一个方法：

```java
CodeGenTypeEnum routeCodeGenType(String userPrompt);
```

这表示它的职责非常单一：

- 它只负责分类；
- 不负责生成代码；
- 不负责保存数据库；
- 不负责返回解释文本。

这就是好设计：**每个类只干一件事**。

#### 第二，返回值直接是枚举

注意，这里不是返回字符串，而是直接返回：

```java
CodeGenTypeEnum
```

这意味着：

- 业务层拿到的不是松散文本；
- 而是受 Java 编译器约束的类型；
- 后续保存数据库时再取 `enum.getValue()` 即可。

这就是“**先做领域建模，再做业务落地**”。

#### 第三，使用普通 `ChatLanguageModel`

路由任务不是长文本生成，也不是复杂流式交互。

它只需要：

- 快速判断；
- 结果唯一；
- 成本低。

所以这里选择：

```java
private ChatLanguageModel chatModel;
```

而不是 `StreamingChatLanguageModel`。

这说明我们不是“为了用 AI 而用 AI”，而是根据任务性质选择模型能力。

---

## 9. 路由 Prompt 为什么这样写？你要学会 Prompt 设计原则

`src/main/resources/prompt/codegen-routing-system-prompt.txt`

```text
你是一个代码生成方案路由助手。你的任务不是生成代码，而是根据用户的需求描述，从以下三个生成类型中严格选择一个最合适的结果。

可选结果只有：
- SINGLE_FILE
- MULTI_FILE
- VUE_PROJECT

判断规则：
- 如果需求明显只是一个简单单页，选择 SINGLE_FILE。
- 如果需求包含多个区块、多个静态页面或更适合 HTML/CSS/JS 拆分维护，选择 MULTI_FILE。
- 如果需求涉及后台、管理系统、复杂交互、表单、数据展示、组件化、路由或未来扩展，选择 VUE_PROJECT。

输出要求：
- 只能返回一个结果。
- 不要解释原因。
- 不要输出多余文本。
- 不要输出 Markdown。
- 不要输出 JSON。
```

### 9.1 为什么我说这份 Prompt 是“工程化 Prompt”？

因为它不是“让模型自由发挥”，而是在做**输出约束设计**。

你要记住一个原则：

> 当 AI 输出要进入程序逻辑时，Prompt 的首要目标不是“文采”，而是“可解析、可预测、可收敛”。

这里做对了几件事：

1. **先定义角色**：你是路由助手，不是代码生成器。
2. **再定义候选集合**：只有三个结果。
3. **再定义判断标准**：什么场景对应什么结果。
4. **最后定义输出边界**：只能一个结果，不解释，不 JSON，不 Markdown。

这就是“提示词像接口文档一样写”。

### 9.2 为什么不要 JSON？

因为这次任务只需要一个枚举值。

如果你硬要让模型返回：

```json
{"type": "VUE_PROJECT", "reason": "..."}
```

会带来三个额外问题：

- 增加解析复杂度；
- 增加模型偏离格式的概率；
- 在 DeepSeek 这类模型上，还可能碰到 JSON 模式配置约束。

所以这里选择“只返回枚举名”，是最符合 YAGNI 的做法。

---

## 10. AI 路由真正落地的位置：`AppServiceImpl#createApp()`

`src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

```java
@Override
public Long createApp(AppAddRequest appAddRequest, User loginUser) {
    ThrowUtils.throwIf(appAddRequest == null, ErrorCode.PARAMS_ERROR, "请求参数不能为空");
    ThrowUtils.throwIf(loginUser == null || loginUser.getId() == null, ErrorCode.NOT_LOGIN_ERROR, "用户未登录");
    String initPrompt = StrUtil.trim(appAddRequest.getInitPrompt());
    ThrowUtils.throwIf(StrUtil.isBlank(initPrompt), ErrorCode.PARAMS_ERROR, "初始化 prompt 不能为空");
    CodeGenTypeEnum codeGenTypeEnum = resolveCodeGenType(appAddRequest.getCodeGenType(), initPrompt);
    App app = new App();
    app.setAppName(initPrompt.substring(0, Math.min(initPrompt.length(), 12)));
    app.setInitPrompt(initPrompt);
    app.setCodeGenType(codeGenTypeEnum.getValue());
    app.setUserId(loginUser.getId());
    app.setPriority(AppConstant.DEFAULT_APP_PRIORITY);
    boolean saveResult = this.save(app);
    ThrowUtils.throwIf(!saveResult, ErrorCode.OPERATION_ERROR, "创建应用失败");
    return app.getId();
}
```

配套的路由方法：

```java
private CodeGenTypeEnum resolveCodeGenType(String requestCodeGenType, String initPrompt) {
    if (StrUtil.isNotBlank(requestCodeGenType)) {
        CodeGenTypeEnum codeGenTypeEnum = parseCodeGenType(requestCodeGenType);
        ThrowUtils.throwIf(codeGenTypeEnum == null, ErrorCode.PARAMS_ERROR, "代码生成类型错误");
        return codeGenTypeEnum;
    }
    try {
        AiCodeGenTypeRoutingService routingService = aiCodeGenTypeRoutingServiceFactory.createService();
        CodeGenTypeEnum routed = routingService.routeCodeGenType(initPrompt);
        if (routed != null) {
            return routed;
        }
    } catch (Exception e) {
        log.warn("AI 路由失败，将使用兜底模式, prompt={}", initPrompt, e);
    }
    return CodeGenTypeEnum.MULTI_FILE;
}
```

### 10.1 这里你要记住三个优先级

这个方法非常值得你背下来，因为它体现了业务优先级设计：

```text
显式指定 > AI 路由 > 默认兜底
```

为什么这么设计？

- **显式指定优先**：管理员、调试场景必须可控。
- **AI 路由其次**：普通用户获得最好的默认体验。
- **默认兜底最后**：当模型异常时，系统不能直接挂掉。

这就是“稳健的 AI 集成思维”——AI 是增强层，不应成为单点故障源。

---

## 11. 封面生成链路：这部分是典型的平台异步资产处理

现在我们讲第二条大链路：**部署后自动生成封面图**。

这条链路拆开看，其实是 4 步：

1. 配置截图与 COS 参数。
2. 启动无头浏览器截图并压缩。
3. 上传到 COS，得到外网 URL。
4. 部署成功后异步触发，并把结果回写到 `app.cover`。

后来又加了：

5. 记录任务状态、失败原因、重试次数。

---

## 12. 配置层：先把参数对象建起来，不要写死

`src/main/resources/application.yml`

```yml
app:
  screenshot:
    temp-dir: ${user.dir}/temp/screenshots
    width: 1600
    height: 900
    wait-after-load-millis: 2000
    compression-quality: 0.3
    upload-prefix: /screenshots
    max-retries: 3
    retry-delay-millis: 3000

cos:
  client:
    host: ${COS_HOST:https://your-cdn-or-cos-domain.com}
    secret-id: ${COS_SECRET_ID:}
    secret-key: ${COS_SECRET_KEY:}
    region: ${COS_REGION:ap-shanghai}
    bucket: ${COS_BUCKET:}
```

对应 Java 配置类：

`src/main/java/com/adcage/acaicodefree/config/properties/ScreenshotProperties.java`

```java
@ConfigurationProperties(prefix = "app.screenshot")
public class ScreenshotProperties {
    private String tempDir;
    private Integer width;
    private Integer height;
    private Long waitAfterLoadMillis;
    private Float compressionQuality;
    private String uploadPrefix;
    private Integer maxRetries;
    private Long retryDelayMillis;
}
```

### 12.1 为什么一定要建 `Properties` 类？

因为配置项一旦超过 2~3 个，如果你还用 `@Value` 一个个注入，很快就会失控。

`Properties` 类的好处是：

- 配置结构和 yml 结构一一对应；
- IDE 自动提示更好；
- 以后扩展参数更容易；
- 单元测试里也能直接 new 一个配置对象塞进去。

这就是 Spring Boot 推荐的“**配置对象化**”实践。

---

## 13. COS 客户端为什么要单独封装两层？

### 13.1 第一层：配置出 `COSClient`

`src/main/java/com/adcage/acaicodefree/config/CosClientConfig.java`

```java
@Configuration
@EnableConfigurationProperties(CosClientProperties.class)
public class CosClientConfig {

    @Bean(destroyMethod = "shutdown")
    public COSClient cosClient(CosClientProperties cosClientProperties) {
        COSCredentials cosCredentials = new BasicCOSCredentials(
                cosClientProperties.getSecretId(),
                cosClientProperties.getSecretKey());
        com.qcloud.cos.ClientConfig clientConfig = new com.qcloud.cos.ClientConfig(
                new Region(cosClientProperties.getRegion()));
        return new COSClient(cosCredentials, clientConfig);
    }
}
```

### 13.2 第二层：业务侧只面对 `CosManager`

`src/main/java/com/adcage/acaicodefree/manager/CosManager.java`

```java
@Component
public class CosManager {

    @Resource
    private COSClient cosClient;

    @Resource
    private CosClientProperties cosClientProperties;

    public String uploadFile(String key, File file) {
        if (file == null || !file.exists() || !file.isFile()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "上传文件不存在");
        }
        if (StrUtil.hasBlank(cosClientProperties.getBucket(), cosClientProperties.getHost())) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "COS 配置不完整，请检查 bucket 和 host");
        }
        String normalizedKey = normalizeKey(key);
        PutObjectRequest putObjectRequest = new PutObjectRequest(cosClientProperties.getBucket(), normalizedKey, file);
        cosClient.putObject(putObjectRequest);
        return buildFileUrl(normalizedKey);
    }
}
```

### 13.3 为什么不能在业务代码里直接 `new PutObjectRequest(...)`？

因为那样会把第三方 SDK 细节污染到业务层。

这里的封装思路很专业：

- `CosClientConfig` 负责“怎么创建 SDK 客户端”；
- `CosManager` 负责“怎么和 COS 交互”；
- `ScreenshotServiceImpl` 负责“截图业务流程”；
- `AppServiceImpl` 负责“什么时候触发截图”。

这叫做**按职责分层**。

如果以后从 COS 改成阿里 OSS、MinIO、S3，你只需要动 Manager/Config 层，而不是把业务代码全项目翻一遍。

---

## 14. 截图工具：为什么不是简单保存一张 PNG 就结束？

`src/main/java/com/adcage/acaicodefree/utils/WebScreenshotUtils.java`

```java
public static File captureAndCompress(String url, String tempDir, Integer width, Integer height,
                                      Long waitAfterLoadMillis, Float compressionQuality) throws IOException {
    WebDriverManager.chromedriver().setup();
    File targetDir = new File(tempDir, DATE_FORMATTER.format(LocalDate.now()));
    FileUtil.mkdir(targetDir);
    String fileId = IdUtil.simpleUUID();
    File rawFile = new File(targetDir, fileId + ".png");
    File compressedFile = new File(targetDir, fileId + "_compressed.jpg");
    WebDriver webDriver = null;
    try {
        ChromeOptions chromeOptions = new ChromeOptions();
        chromeOptions.addArguments("--headless=new");
        chromeOptions.addArguments("--disable-gpu");
        chromeOptions.addArguments("--no-sandbox");
        chromeOptions.addArguments("--disable-dev-shm-usage");
        chromeOptions.addArguments("--disable-extensions");
        chromeOptions.addArguments(String.format("--window-size=%d,%d", width, height));
        webDriver = new ChromeDriver(chromeOptions);
        webDriver.get(url);
        waitForPageFullyRendered(webDriver, waitAfterLoadMillis);
        File screenshot = ((TakesScreenshot) webDriver).getScreenshotAs(OutputType.FILE);
        FileUtil.copy(screenshot, rawFile, true);
        compressToJpg(rawFile, compressedFile, compressionQuality);
        return compressedFile;
    } finally {
        if (webDriver != null) {
            webDriver.quit();
        }
        deleteIfExists(rawFile);
    }
}
```

### 14.1 这一段你要理解 4 个关键点

#### 第一，`WebDriverManager.chromedriver().setup()`

它帮我们自动准备浏览器驱动。

否则你需要自己手动下载、配置版本、维护路径，非常麻烦。

#### 第二，`ChromeOptions` 是线上稳定性的关键

特别是：

- `--headless=new`
- `--no-sandbox`
- `--disable-dev-shm-usage`

这不是“随便写几个参数”，而是为 Linux / Docker / CI 环境做兼容。

#### 第三，页面等待不是只看 `get(url)` 完成

配套方法：

```java
private static void waitForPageFullyRendered(WebDriver webDriver, Long waitAfterLoadMillis) {
    new WebDriverWait(webDriver, Duration.ofSeconds(15)).until(driver -> {
        Object readyState = ((JavascriptExecutor) driver).executeScript("return document.readyState");
        return "complete".equals(readyState);
    });
    if (waitAfterLoadMillis != null && waitAfterLoadMillis > 0) {
        Thread.sleep(waitAfterLoadMillis);
    }
}
```

这是“两段等待”：

- 第一段：浏览器文档 ready；
- 第二段：再等一会儿，让异步资源、骨架屏、动画稳定。

这就是为什么你看到的封面更可靠。

#### 第四，先截图，再压缩，再删除原始文件

这体现的是平台思维：

- 列表页不需要原图级质量；
- 用户更需要加载快；
- 存储成本也要控制。

所以最终上传的是压缩后的 JPG，而不是原始 PNG。

---

## 15. 截图业务服务：为什么单独再包一层？

`src/main/java/com/adcage/acaicodefree/service/impl/ScreenshotServiceImpl.java`

```java
@Override
public String generateAndUploadCover(Long appId, String appUrl) {
    if (appId == null || appId <= 0) {
        throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用 id 不合法");
    }
    if (StrUtil.isBlank(appUrl)) {
        throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用访问地址不能为空");
    }
    File compressedFile = null;
    try {
        compressedFile = captureCompressedFile(appUrl);
        String objectKey = buildObjectKey(compressedFile.getName());
        return cosManager.uploadFile(objectKey, compressedFile);
    } catch (Exception e) {
        log.error("生成应用封面失败, appId={}, appUrl={}", appId, appUrl, e);
        throw new BusinessException(ErrorCode.OPERATION_ERROR, "生成封面失败: " + e.getMessage());
    } finally {
        WebScreenshotUtils.deleteIfExists(compressedFile);
    }
}
```

### 15.1 这层服务的价值是什么？

它把：

- 截图工具调用
- COS 上传
- 临时文件清理

合成了一个统一方法：

```java
String generateAndUploadCover(Long appId, String appUrl)
```

从调用方角度看，它只关心一件事：

> 传入 appId 和访问地址，能不能拿到一个外网封面 URL。

这就是“对外隐藏内部步骤”。

你可以把它看成典型的**业务子流程封装**。

---

## 16. 部署后异步封面：为什么不是同步做？

如果你把截图逻辑直接写进 `deployApp()` 主线程里，会产生三个问题：

1. 用户点击部署后，要等截图、压缩、上传全做完才能返回。
2. 一旦截图失败，部署结果会被连带拖垮。
3. Selenium 是重资源任务，不适合直接堵在接口响应链路里。

所以我们采用了：

> 部署成功先返回；封面生成异步执行。

核心代码在 `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`：

```java
boolean updateResult = this.updateById(updateApp);
ThrowUtils.throwIf(!updateResult, ErrorCode.OPERATION_ERROR, "更新应用部署信息失败");
triggerCoverGenerationAsync(appId, deployKey);
return buildDeployUrl(deployKey);
```

### 16.1 为什么这里用了单线程执行器？

```java
private final ExecutorService screenshotTaskExecutor = Executors.newSingleThreadExecutor(
        Thread.ofVirtual().name("screenshot-task-", 0).factory());
```

这是一种非常务实的折中：

- **对外是异步**：接口不阻塞；
- **对内是串行**：避免多个 Selenium 任务同时抢浏览器资源；
- **用虚拟线程**：线程管理成本更低。

这里不是为了“炫技”，而是为了稳定性。

在 MVP 阶段，串行往往比高并发更靠谱。

---

## 17. 后续增强：为什么又补了“状态 + 重试”？

最初异步封面链路已经能跑通，但有一个体验问题：

- 前端只知道“部署成功了”；
- 但不知道“封面任务现在进行到哪一步”；
- 如果截图失败，也看不到原因。

于是后面又补了这组能力：

- `PENDING`
- `RUNNING`
- `SUCCESS`
- `FAILED`
- 重试次数
- 错误信息

### 17.1 任务状态核心代码

`src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

```java
private void triggerCoverGenerationAsync(Long appId, String deployKey) {
    updateCoverTaskState(appId, "PENDING", 0, null);
    screenshotTaskExecutor.submit(() -> {
        int maxRetries = screenshotProperties.getMaxRetries() == null ? 3 : Math.max(screenshotProperties.getMaxRetries(), 1);
        long retryDelayMillis = screenshotProperties.getRetryDelayMillis() == null ? 3000L : Math.max(screenshotProperties.getRetryDelayMillis(), 0L);
        String deployUrl = buildDeployUrl(deployKey);
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            updateCoverTaskState(appId, "RUNNING", attempt, null);
            try {
                String coverUrl = screenshotService.generateAndUploadCover(appId, deployUrl);
                if (StrUtil.isBlank(coverUrl)) {
                    updateCoverTaskState(appId, "FAILED", attempt, "封面地址为空");
                    continue;
                }
                App updateApp = new App();
                updateApp.setId(appId);
                updateApp.setCover(coverUrl);
                boolean updated = this.updateById(updateApp);
                if (!updated) {
                    updateCoverTaskState(appId, "FAILED", attempt, "封面地址回写失败");
                    continue;
                }
                updateCoverTaskState(appId, "SUCCESS", attempt, null);
                return;
            } catch (Exception e) {
                updateCoverTaskState(appId, "FAILED", attempt, e.getMessage());
                if (attempt < maxRetries && retryDelayMillis > 0) {
                    Thread.sleep(retryDelayMillis);
                }
            }
        }
    });
}
```

### 17.2 这个设计好在哪里？

#### 第一，好观察

状态被挂到 `AppVO`：

`src/main/java/com/adcage/acaicodefree/model/vo/app/AppVO.java`

```java
private String coverTaskStatus;
private Integer coverRetryCount;
private String coverErrorMessage;
```

于是前端不再只能“猜”，而是可以直接显示真实任务状态。

#### 第二，好恢复

失败不是一次就放弃，而是可重试。

这在 Selenium / 网络上传这种不稳定链路里非常重要。

#### 第三，好扩展

今天我们用的是内存态 `coverTaskStateMap`；
以后你完全可以把它迁移成：

- 数据库字段
- 独立任务表
- MQ 消费状态

也就是说，当前方案虽然简单，但**演进方向是清晰的**。

---

## 18. 源码下载：为什么不是把目录直接暴露出去？

源码下载最容易犯的错误是：

- 直接让用户访问文件目录；
- 或者把整个生成目录原样打包。

这会带来两个问题：

1. 泄露不该下载的内容；
2. 下载包体积失控。

所以我们把下载能力封装成专门服务。

### 18.1 控制器入口

`src/main/java/com/adcage/acaicodefree/controller/AppController.java`

```java
@GetMapping("/download/{appId}")
public void downloadAppProject(@PathVariable Long appId, HttpServletRequest request, HttpServletResponse response) {
    ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 无效");
    User loginUser = userService.getLoginUser(request);
    App app = appService.getById(appId);
    ThrowUtils.throwIf(app == null, ErrorCode.NOT_FOUND_ERROR, "应用不存在");
    ThrowUtils.throwIf(!app.getUserId().equals(loginUser.getId()), ErrorCode.NO_AUTH_ERROR, "仅允许下载本人应用源码");
    String codeGenType = app.getCodeGenType();
    Path sourceDir;
    if (CodeGenTypeEnum.VUE_PROJECT.getValue().equals(codeGenType)) {
        sourceDir = AppConstant.getVueProjectOutputDir(appId);
    } else {
        sourceDir = AppConstant.getCodeOutputRootPath().resolve(codeGenType + "_" + appId);
    }
    String fileName = "app-" + appId + ".zip";
    projectDownloadService.writeProjectZipToResponse(sourceDir, fileName, response);
}
```

### 18.2 真正的过滤逻辑

`src/main/java/com/adcage/acaicodefree/service/impl/ProjectDownloadServiceImpl.java`

```java
private static final Set<String> EXCLUDED_DIRS = Set.of(
        "node_modules", ".git", "dist", "build", "target", ".mvn", ".idea", ".vscode", ".cache");

private static final Set<String> EXCLUDED_FILE_NAMES = Set.of(".ds_store", ".env");

private static final Set<String> EXCLUDED_FILE_EXTENSIONS = Set.of(".log", ".tmp", ".cache");
```

以及：

```java
ZipUtil.zip(tempZipFile, StandardCharsets.UTF_8, true, this::shouldInclude, sourceFile);
response.setContentType("application/zip");
response.setHeader("Content-Disposition", buildContentDisposition(safeFileName));
```

### 18.3 你要理解的设计思想

- 下载的是**源码目录**，不是部署目录。
- 过滤逻辑必须在**服务端**，不能让前端“自觉忽略”。
- 下载接口直接写二进制响应，不能再包 `BaseResponse<T>`。

这三个点非常关键。

---

## 19. 前端为什么一定要改首页？

如果前端还继续这样写：

```ts
addApp({
  initPrompt: searchText.value,
  codeGenType: 'vue_project',
})
```

那么后端的 AI 路由永远没有机会生效。

所以首页改成了：

`ac-ai-code-free-fronted/src/pages/HomePage.vue`

```ts
const res = await addApp({
  initPrompt: searchText.value,
})
```

### 19.1 这意味着什么？

这代表系统设计真正从：

> “前端决定模式，后端照做”

变成了：

> “前端只表达需求，后端负责智能编排”

这才是平台该有的形态。

---

## 20. 前端详情页：为什么展示“状态”比展示“字段”更重要？

`ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`

### 20.1 顶部状态展示

```vue
<a-tag v-if="app?.coverTaskStatus" :color="coverTaskStatusColor(app.coverTaskStatus)">
  {{ formatCoverTaskStatus(app.coverTaskStatus, app.coverRetryCount) }}
</a-tag>
<a-tag v-if="app?.codeGenType" color="blue">{{ formatCodeGenType(app.codeGenType) }}</a-tag>
<a-button :loading="downloadLoading" :disabled="!canDownload" @click="doDownload" class="download-btn">
  <template #icon><download-outlined /></template>
  下载代码
</a-button>
```

### 20.2 下载逻辑

```ts
const doDownload = async () => {
  if (!canDownload.value) {
    message.warning('仅应用创建者可以下载源码')
    return
  }
  const response = await fetch(`${baseUrl}/app/download/${appId}`, {
    method: 'GET',
    credentials: 'include',
  })
  const contentDisposition = response.headers.get('Content-Disposition') || ''
  const fileNameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  const fileName = fileNameMatch?.[1] ? decodeURIComponent(fileNameMatch[1]) : `app-${appId}.zip`
  const blob = await response.blob()
  const blobUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = fileName
  link.click()
}
```

### 20.3 为什么这里用 `fetch` 而不是继续走通用 Axios 封装？

因为下载场景和 JSON 接口不是一回事。

下载接口要处理的是：

- 二进制流；
- 原始响应头；
- 文件名解析；
- Blob 下载。

这时候 `fetch` 反而更直接，更少“框架封装副作用”。

### 20.4 部署后的轮询

```ts
const pollCoverAfterDeploy = async () => {
  let count = 0
  const maxCount = 8
  const timer = setInterval(async () => {
    count += 1
    await loadApp()
    if (app.value?.cover || app.value?.coverTaskStatus === 'FAILED' || count >= maxCount) {
      if (app.value?.coverTaskStatus === 'FAILED' && app.value?.coverErrorMessage) {
        message.warning(`封面生成失败：${app.value.coverErrorMessage}`)
      }
      clearInterval(timer)
    }
  }, 4000)
}
```

这段轮询的意义不是“技术上炫酷”，而是解决用户认知问题：

- 封面是异步生成的；
- 如果不刷新，用户看不到变化；
- 如果失败，也应该让用户知道失败原因。

这就是“平台状态可感知”。

---

## 21. 前端卡片为什么也要补权限标签？

`ac-ai-code-free-fronted/src/components/AppCard.vue`

```vue
<a-tag color="blue" size="small" v-if="app.codeGenType">{{ formatCodeGenType(app.codeGenType) }}</a-tag>
<a-tag :color="isOwner ? 'green' : 'default'" size="small">{{ isOwner ? '可下载源码' : '仅作者可下载' }}</a-tag>
```

这看起来像“小改动”，但它非常体现产品意识。

因为如果你只在详情页里做权限限制，而列表页没有任何提示，用户会产生困惑：

- 为什么这个作品我点进去不能下载？
- 是系统坏了，还是我没权限？

卡片上提前说明权限，本质上是在降低用户误解成本。

---

## 22. 依赖层还有一个很关键的工程修复：`okio` 冲突

`pom.xml`

```xml
<dependency>
    <groupId>com.qcloud</groupId>
    <artifactId>cos_api</artifactId>
    <version>5.6.227</version>
    <exclusions>
        <exclusion>
            <groupId>com.squareup.okio</groupId>
            <artifactId>okio</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>com.squareup.okio</groupId>
    <artifactId>okio-jvm</artifactId>
    <version>3.9.0</version>
</dependency>
```

### 22.1 为什么这里值得特别讲？

因为这是一个很典型的 Java 依赖冲突问题。

现象是：

- LangChain4j 依赖的新版本 `okhttp/okio`；
- COS SDK 传递依赖了旧版 `okio`；
- 最终运行时出现 `NoSuchFieldError: okio.Options$Companion`。

这不是业务 bug，而是**依赖树冲突**。

解决思路不是瞎改代码，而是：

1. 找到冲突来源；
2. 排除旧版本；
3. 显式引入兼容的新版本。

这是你以后做 Java 工程必须具备的能力：

> 看到运行时类冲突，优先查依赖树，而不是怀疑业务逻辑。

---

## 23. 测试：这一阶段不是“写完就算”，而是补了自动化闭环

### 23.1 封面状态与重试测试

`src/test/java/com/adcage/acaicodefree/service/impl/AppServiceCoverTaskStateTest.java`

```java
Mockito.when(screenshotService.generateAndUploadCover(Mockito.eq(1L), Mockito.anyString()))
        .thenThrow(new RuntimeException("first fail"))
        .thenReturn("https://cdn.example.com/cover.jpg");

ReflectionTestUtils.invokeMethod(appService, "triggerCoverGenerationAsync", 1L, "abc123");
waitForFinalState(appService, 1L);

AppVO appVO = appService.getAppVO(app);
Assertions.assertEquals("SUCCESS", appVO.getCoverTaskStatus());
Assertions.assertEquals(2, appVO.getCoverRetryCount());
```

这个测试验证的是：

- 第一次失败；
- 第二次成功；
- 最终状态应为 `SUCCESS`；
- 重试次数应正确记录。

另一条测试则验证“多次失败后应停在 `FAILED`”。

这就把“重试逻辑”从主观判断变成了可回归验证的行为。

### 23.2 前后端端到端测试

`ac-ai-code-free-fronted/tests/chat-flow.e2e.test.mjs`

```js
const addAppBody = {
  initPrompt: prompt,
  ...(codeGenType ? { codeGenType } : {}),
}
const addAppRes = await postJson('/app/add', addAppBody, cookie)
const appDetailRes = await getJson(`/app/get/vo?id=${appId}`, cookie)
assert.ok(appDetailRes.data?.data?.codeGenType, '创建应用后应有生成类型')

const downloadResponse = await fetch(`${BASE_URL}/app/download/${appId}`, {
  method: 'GET',
  headers: { Cookie: cookie },
})
assert.equal(downloadResponse.status, 200)
assert.ok(downloadContentType.includes('application/zip'))
```

这个 E2E 很重要，因为它验证的不是“某个方法能跑”，而是：

```text
注册 -> 登录 -> 创建应用 -> 查询详情 -> 验证 AI 路由结果 -> SSE 会话 -> 下载源码
```

也就是说，它验证的是**完整链路**。

这类测试才最能证明“平台功能真的闭环了”。

---

## 24. 最后，站在老师的角度，我希望你真正学会的不是代码，而是方法

读完这一阶段，你最应该带走的不是几个类名，而是以下 8 个方法论：

### 24.1 业务编排一定收敛到 Service

Controller 不要承载复杂业务，它只负责进出站。

### 24.2 AI 接入要遵循“显式优先、AI 兜底、默认保底”

不要把 AI 当成唯一真理源，否则系统稳定性会被模型绑架。

### 24.3 LangChain4j 的最佳用法是声明式接口，而不是手写 HTTP

你应该把 AI 能力抽象成 Java 接口、Prompt 资源、工厂装配，而不是散落的字符串请求。

### 24.4 Prompt 不是文案，是协议

当输出要进程序逻辑时，Prompt 的首要目标是可收敛，不是花哨。

### 24.5 第三方 SDK 一定做隔离层

COS、Selenium、甚至未来的 OSS、S3，都不应该直接污染业务流程代码。

### 24.6 异步任务要考虑可观测性

异步不是“丢出去就不管”，而是要补状态、错误信息、重试次数。

### 24.7 文件下载要按“源码交付”思维设计

不是能下载就行，而是要下载正确的内容、过滤错误的内容、返回正确的头。

### 24.8 平台体验不是只靠后端功能，前端必须把状态讲清楚

用户不懂你后台做了多少事，他只看见：

- 现在是什么状态；
- 我能不能下载；
- 为什么失败；
- 下一步该做什么。

这就是产品化交付。

---

## 25. 本阶段验证结果（真实执行过）

这部分不是推测，是实际执行过的验证结论：

- 后端全量测试：`mvn test` 通过
- 前端构建验证：`npm run build` 通过
- 端到端测试：启动后端后执行 `npm run test:e2e:chat` 通过

验证覆盖到的重点包括：

- AI 路由结果能落到应用详情
- 聊天 SSE 链路正常
- Vue 工程模式流式消息契约正常
- 源码下载接口正常返回 ZIP
- 封面异步任务重试状态机行为正确

---

## 26. 一句话总结这次第八阶段

如果你让我用一句话概括这次实现，我会这样说：

> 第八阶段真正完成的，不是“加了封面、下载、路由三个功能”，而是把平台从“生成代码工具”升级成了“能自动选路、能交付源码、能管理作品状态的应用工坊”。

而从工程角度看，这次最值得学的核心，是：

> 用 LangChain4j 做声明式 AI 能力，用 Service 做业务编排，用异步状态机做平台任务管理，用前端状态展示把复杂后端行为讲给用户听。

如果你把这一整套思路学会了，那么你以后再做：

- AI 模板推荐
- AI 组件路由
- AI 工作流编排
- 异步图像处理
- 文件导出/交付

都会容易很多。
