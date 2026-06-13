# Java AI Legacy 代码隔离设计

## 背景

ac-ai-code-free 项目中，所有 AI 核心能力已迁移到 Python Agent Runtime，Java 端的 LangChain4j AI 代码已全部废弃（@Deprecated）。但废弃代码仍散布在 `ai/`、`core/`、`runtime/impl/`、`config/`、`workflow/` 等目录中，与活跃业务代码交叉混合，不利于维护和理解。

## 目标

将所有废弃的 Java AI 代码隔离到统一的 `legacy/` 包下，使其不干扰主要业务代码。活跃代码（gRPC Bridge、SSE DTO、Runtime 路由、流处理器等）保留在原位。

## 约束

- 废弃代码保留不删除（用户要求保留）
- 活跃业务功能不能受影响
- 尽量减少对活跃代码的侵入性修改

## 方案：统一 `legacy/` 顶层包

### 目标结构

```
com.adcage.acaicodefree.legacy/
├── ai/
│   ├── AiCodeGeneratorService.java
│   ├── AiCodeGenServiceFactory.java
│   ├── AiCodeGenTypeRoutingService.java
│   ├── AiCodeGenTypeRoutingServiceFactory.java
│   ├── guardrail/
│   │   ├── PromptSafetyInputGuardrail.java
│   │   └── RetryOutputGuardrail.java
│   ├── model/
│   │   ├── SingleCodeResult.java
│   │   └── MultiFileCodeResult.java
│   └── tools/
│       ├── BaseTool.java
│       ├── ToolManager.java
│       ├── FileReadTool.java
│       ├── FileWriteTool.java
│       ├── FileModifyTool.java
│       ├── FileDeleteTool.java
│       └── FileDirReadTool.java
├── core/
│   ├── AiCodeGeneratorFacade.java
│   ├── CodeParserOld.java
│   └── memory/
│       └── ChatMemoryLoader.java
├── runtime/
│   └── impl/
│       ├── JavaAgentRuntime.java
│       └── PythonAgentRuntime.java
├── config/
│   ├── ReasoningStreamingChatModelConfig.java
│   └── ai/
│       └── RoutingChatModelConfig.java
└── workflow/
    ├── ai/
    │   ├── ImageCollectionPlanService.java
    │   ├── ImageCollectionPlanServiceFactory.java
    │   ├── ImageCollectionService.java
    │   ├── ImageCollectionServiceFactory.java
    │   ├── PromptEnhancerService.java
    │   └── PromptEnhancerServiceFactory.java
    ├── config/
    │   ├── WorkflowMermaidProperties.java
    │   ├── WorkflowProperties.java
    │   ├── ThreadPoolConfig.java
    │   └── WorkflowToolConfig.java
    ├── controller/
    │   └── WorkflowSseController.java
    ├── model/
    │   ├── ImageCategoryEnum.java
    │   ├── ImageCollectionPlan.java
    │   ├── ImageResource.java
    │   └── QualityResult.java
    ├── node/
    │   ├── CodeGeneratorNode.java
    │   ├── CodeQualityCheckNode.java
    │   ├── ImageCollectorNode.java
    │   ├── ProjectBuilderNode.java
    │   ├── PromptEnhancerNode.java
    │   ├── RouterNode.java
    │   └── concurrent/
    │       ├── ContentImageCollectorNode.java
    │       ├── DiagramCollectorNode.java
    │       ├── ImageAggregatorNode.java
    │       ├── ImagePlanNode.java
    │       ├── IllustrationCollectorNode.java
    │       └── LogoCollectorNode.java
    ├── service/
    │   ├── CodeGenConcurrentWorkflow.java
    │   ├── CodeGenWorkflow.java
    │   ├── SimpleWorkflowApp.java
    │   ├── WorkflowCodeGeneratorService.java
    │   └── WorkflowStreamEvent.java
    ├── state/
    │   └── WorkflowContext.java
    └── tool/
        ├── ImageSearchTool.java
        ├── LogoGeneratorTool.java
        ├── MermaidDiagramTool.java
        ├── ObjectStorageManager.java
        └── UndrawIllustrationTool.java
```

### 移动后原目录保留的活跃代码

```
ai/
└── model/
    └── message/
        ├── AiResponseMessage.java
        ├── StreamMessage.java
        ├── StreamMessageTypeEnum.java
        ├── ToolExecutedMessage.java
        └── ToolRequestMessage.java

core/
├── CodeFileSaver.java
├── VisualEditPromptHelper.java
├── build/
│   └── VueProjectBuildService.java
├── handler/
│   ├── JsonMessageStreamHandler.java
│   ├── SimpleTextStreamHandler.java
│   └── StreamHandlerExecutor.java
├── parser/
│   ├── CodePaser.java
│   ├── CodeParserExcutor.java
│   ├── MultiFileParser.java
│   └── SingleFileParser.java
└── saver/
    ├── AbstractCodeFileSaver.java
    ├── CodeFileSaverExecutor.java
    ├── MultiCodeFileSaver.java
    └── SingleCodeFileSaver.java

runtime/
├── CodeGenerationRequest.java
├── CodeGenerationRuntime.java
└── CodeGenerationRuntimeRouter.java

config/                    ← 仅保留非 AI 配置
```

## FileTool 迁移与 GrpcToolService 适配

### 问题

5 个 FileTool（FileReadTool/FileWriteTool/FileModifyTool/FileDeleteTool/FileDirReadTool）有双重身份：
1. LangChain4j @Tool 身份：被 legacy `AiCodeGenServiceFactory` 通过 `ToolManager` 注册
2. 文件操作 Service 身份：被活跃 `GrpcToolService` 直接调用

### 解决方案

1. **新建 `FileOperationService`**（放在 `service/` 下）
   - 将 BaseTool + 5 个 FileTool 的核心文件操作逻辑搬入
   - 不依赖任何 LangChain4j 注解
   - 提供方法：`readFile`, `writeFile`, `modifyFile`, `deleteFile`, `readDir`
   - 同时提供 `generateToolRequestResponse(toolName, args)` 和 `generateToolExecutedResult(toolName, args, result)` 方法（从 BaseTool 搬入）

2. **GrpcToolService 适配**
   - 5 个 `@Resource FileXxxTool` → `@Resource FileOperationService`
   - 调用方式从 `fileReadTool.readFile(path, appId, type)` → `fileOperationService.readFile(appId, type, path)`

3. **JsonMessageStreamHandler 适配**
   - `ToolManager` 依赖 → `FileOperationService` 依赖
   - 工具描述文本生成改为调用 `FileOperationService.generateToolRequestResponse/ExecutedResult`

4. **5 个 FileTool + BaseTool + ToolManager 整体移入 `legacy/ai/tools/`**
   - 保持 legacy AI 流程可编译
   - legacy 代码仍通过 `ToolManager` 使用 FileTool 的 @Tool 方法

## 活跃代码的 import 修改

移动后，以下活跃文件需要修改 import 路径：

| 文件 | 需修改的 import |
|------|---------------|
| `GrpcToolService.java` | 移除 `ai.tools.FileXxxTool` import，改用 `FileOperationService` |
| `JsonMessageStreamHandler.java` | 移除 `ai.tools.BaseTool/ToolManager` import，改用 `FileOperationService` |
| `GrpcPythonAgentRuntime.java` | 无需修改（仅依赖 `ai.model.message.*`，不动） |
| `core/parser/*` | `ai.model.SingleCodeResult/MultiFileCodeResult` → `legacy.ai.model.*` |
| `core/saver/*` | `ai.model.SingleCodeResult/MultiFileCodeResult` → `legacy.ai.model.*` |
| `core/CodeFileSaver.java` | `ai.model.SingleCodeResult/MultiFileCodeResult` → `legacy.ai.model.*` |

**注意**：`core/parser/*` 和 `core/saver/*` 依赖 `SingleCodeResult` 和 `MultiFileCodeResult`。这两个类带 LangChain4j `@Description` 注解，但 parser/saver 只用它们的字段，不依赖注解。移动到 `legacy.ai.model` 后，parser/saver 的 import 需要更新为 `legacy.ai.model.*`。

## 测试文件迁移

对应的测试文件也需要迁移到 `legacy/` 包下：

- `test/.../ai/AiCodeGeneratorServiceTest.java` → `test/.../legacy/ai/`
- `test/.../ai/AiCodeGenServiceFactoryTest.java` → `test/.../legacy/ai/`
- `test/.../ai/AiCodeGenTypeRoutingServiceTest.java` → `test/.../legacy/ai/`
- `test/.../ai/ChatJsonTest.java` → `test/.../legacy/ai/`
- `test/.../ai/tools/*` → `test/.../legacy/ai/tools/`
- `test/.../core/AiCodeGeneratorFacadeTest.java` → `test/.../legacy/core/`
- `test/.../core/AiCodeGeneratorFacadeStreamMessageTest.java` → `test/.../legacy/core/`
- `test/.../workflow/**` → `test/.../legacy/workflow/`

约定测试 `JavaAiCoreConventionTest.java` 保留在原位，但需更新扫描路径。

## YAML 配置

`application.yml` 和 `application-local.yml` 中的 LangChain4j 配置段暂时保留，后续清理时再处理。

## 风险与注意事项

1. **package 声明和 import 全量更新**：每个移动文件都需要更新 `package` 声明，所有引用这些文件的地方都需要更新 import。这是机械操作但量大，需仔细检查遗漏。
2. **Spring Bean 扫描**：`legacy/` 下的 `@Component/@Service/@Configuration` 仍会被 Spring Boot 自动扫描注册。隔离后应确认这些 Bean 不会被意外注入到活跃代码中。当前约定测试 `JavaAiCoreConventionTest` 可作为守卫。
3. **`core/parser` 和 `core/saver` 对 legacy model 的依赖**：移动后 `SingleCodeResult` 和 `MultiFileCodeResult` 在 `legacy.ai.model` 包下，活跃的 parser/saver 需要引用 legacy 包。这是一个交叉依赖，后续可考虑将这两个 POJO 去掉 LangChain4j 注解后移回 `ai/model/`。
