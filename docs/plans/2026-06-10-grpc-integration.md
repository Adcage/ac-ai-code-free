# gRPC 集成改造实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用 gRPC 替换 Java 与 Python 之间的 HTTP+SSE 通信，实现两端近乎无感的互相调用——Python 直接调 Java 的工具和平台服务，Java 直接消费 Python 的流式代码生成事件，统一消息类型，消除手动转换。

**Architecture:** 定义 3 个 gRPC 服务——`CodeGenerationService`（Python 暴露）、`ToolService`（Java 暴露）、`PlatformService`（Java 暴露）。两端各自运行 gRPC Server + Client，通过 proto 生成的强类型代码通信。Java 端的 `PythonAgentRuntime` 从 HTTP+SSE 改为 gRPC Server Streaming；Python 端的 `ModelConfigClient` 从 HTTP 回调改为 gRPC Unary 调用；Python 端的 `FileTools` 从本地实现改为 gRPC 远程调用 Java 端的工具。

**Tech Stack:** gRPC-Java (grpc-spring-boot-starter)、grpcio + grpcio-tools (Python)、Protocol Buffers 3、Spring Boot 3.5.5、FastAPI + grpc.aio

---

## 总览

### 阶段划分

| 阶段 | 内容 | 预计改动量 |
|------|------|-----------|
| Phase 1 | Proto 定义 + 代码生成基础设施 | 新增 proto 文件 + 构建配置 |
| Phase 2 | Java gRPC Server（ToolService + PlatformService） | 新增 Server 实现 + 修改 pom.xml |
| Phase 3 | Python gRPC Server（CodeGenerationService） | 新增 Server 实现 + 修改 pyproject.toml |
| Phase 4 | Java gRPC Client（替代 PythonAgentRuntime） | 修改 runtime 层 |
| Phase 5 | Python gRPC Client（替代 ModelConfigClient + FileTools） | 修改 services + agent 层 |
| Phase 6 | 统一事件流 + 清理旧代码 | 修改 AppServiceImpl + 删除旧文件 |

### 依赖关系

```
Phase 1 ──► Phase 2 ──► Phase 4
      │                         │
      └──► Phase 3 ──► Phase 5 │
                              │
                     Phase 6 ◄─┘
```

Phase 2 和 Phase 3 可以并行开发。Phase 4 依赖 Phase 2+3（需要两端 Server 都就绪）。Phase 5 依赖 Phase 3。Phase 6 依赖 Phase 4+5。

---

## Phase 1: Proto 定义 + 代码生成基础设施

### Task 1.1: 创建 proto 文件目录结构

**Files:**
- Create: `proto/code_generation.proto`
- Create: `proto/tool_service.proto`
- Create: `proto/platform_service.proto`
- Create: `proto/common.proto`

**Step 1: 创建 proto 目录**

```bash
mkdir -p proto
```

**Step 2: 创建 common.proto**

定义跨服务共享的消息类型和枚举。

```protobuf
syntax = "proto3";

package com.adcage.acaicodefree;

option java_multiple_files = true;
option java_package = "com.adcage.acaicodefree.grpc.common";

enum CodeGenType {
  CODE_GEN_TYPE_UNSPECIFIED = 0;
  SINGLE_FILE = 1;
  MULTI_FILE = 2;
  VUE_PROJECT = 3;
}

enum EventType {
  EVENT_TYPE_UNSPECIFIED = 0;
  AGENT_START = 1;
  AI_RESPONSE = 2;
  TOOL_REQUEST = 3;
  TOOL_EXECUTED = 4;
  ERROR = 5;
  DONE = 6;
}

message AiResponseData {
  string text = 1;
  bool fallback = 2;
}

message ToolRequestData {
  string id = 1;
  string name = 2;
  string arguments = 3;
}

message ToolExecutedData {
  string id = 1;
  string name = 2;
  string arguments = 3;
  string result = 4;
}

message ErrorData {
  string message = 1;
  int32 code = 2;
}

message DoneData {
  string message = 1;
}
```

**Step 3: 创建 code_generation.proto**

```protobuf
syntax = "proto3";

package com.adcage.acaicodefree;

import "common.proto";

option java_multiple_files = true;
option java_package = "com.adcage.acaicodefree.grpc.codegen";

service CodeGenerationService {
  rpc StreamGenerate(CodeGenerationRequest) returns (stream CodeGenerationEvent);
  rpc StreamModify(CodeModificationRequest) returns (stream CodeGenerationEvent);
  rpc RouteCodeGenType(RouteCodeGenTypeRequest) returns (RouteCodeGenTypeResponse);
  rpc ValidatePrompt(ValidatePromptRequest) returns (ValidatePromptResponse);
}

message CodeGenerationRequest {
  string agent_run_id = 1;
  int64 app_id = 2;
  int64 session_id = 3;
  int64 user_id = 4;
  string prompt = 5;
  CodeGenType code_gen_type = 6;
  string workspace_path = 7;
  int64 model_config_id = 8;
  int32 config_version = 9;
}

message CodeModificationRequest {
  string agent_run_id = 1;
  int64 app_id = 2;
  int64 session_id = 3;
  int64 user_id = 4;
  string prompt = 5;
  CodeGenType code_gen_type = 6;
  string workspace_path = 7;
  int64 model_config_id = 8;
  int32 config_version = 9;
  string original_content = 10;
}

message CodeGenerationEvent {
  string agent_run_id = 1;
  int64 seq = 2;
  EventType event_type = 3;
  oneof payload {
    AiResponseData ai_response = 4;
    ToolRequestData tool_request = 5;
    ToolExecutedData tool_executed = 6;
    ErrorData error = 7;
    DoneData done = 8;
  }
}

message RouteCodeGenTypeRequest {
  string prompt = 1;
}

message RouteCodeGenTypeResponse {
  CodeGenType code_gen_type = 1;
}

message ValidatePromptRequest {
  string prompt = 1;
}

message ValidatePromptResponse {
  bool valid = 1;
  string reason = 2;
}
```

**Step 4: 创建 tool_service.proto**

```protobuf
syntax = "proto3";

package com.adcage.acaicodefree;

option java_multiple_files = true;
option java_package = "com.adcage.acaicodefree.grpc.tool";

service ToolService {
  rpc ReadFile(ReadFileRequest) returns (ReadFileResponse);
  rpc WriteFile(WriteFileRequest) returns (WriteFileResponse);
  rpc ModifyFile(ModifyFileRequest) returns (ModifyFileResponse);
  rpc DeleteFile(DeleteFileRequest) returns (DeleteFileResponse);
  rpc ReadDir(ReadDirRequest) returns (ReadDirResponse);
  rpc StreamWriteFiles(stream WriteFileRequest) returns (BatchWriteResponse);
}

message ReadFileRequest {
  int64 app_id = 1;
  CodeGenType code_gen_type = 2;
  string relative_path = 3;
}

message ReadFileResponse {
  string content = 1;
}

message WriteFileRequest {
  int64 app_id = 1;
  CodeGenType code_gen_type = 2;
  string relative_path = 3;
  string content = 4;
}

message WriteFileResponse {
  string message = 1;
}

message ModifyFileRequest {
  int64 app_id = 1;
  CodeGenType code_gen_type = 2;
  string relative_path = 3;
  string old_content = 4;
  string new_content = 5;
}

message ModifyFileResponse {
  string message = 1;
}

message DeleteFileRequest {
  int64 app_id = 1;
  CodeGenType code_gen_type = 2;
  string relative_path = 3;
}

message DeleteFileResponse {
  string message = 1;
}

message ReadDirRequest {
  int64 app_id = 1;
  CodeGenType code_gen_type = 2;
  string relative_path = 3;
}

message ReadDirResponse {
  string entries = 1;
}

message BatchWriteResponse {
  int32 success_count = 1;
  int32 failure_count = 2;
  repeated string messages = 3;
}
```

**Step 5: 创建 platform_service.proto**

```protobuf
syntax = "proto3";

package com.adcage.acaicodefree;

option java_multiple_files = true;
option java_package = "com.adcage.acaicodefree.grpc.platform";

service PlatformService {
  rpc GetModelConfig(GetModelConfigRequest) returns (GetModelConfigResponse);
  rpc BuildVueProject(BuildVueProjectRequest) returns (BuildVueProjectResponse);
  rpc DeployApp(DeployAppRequest) returns (DeployAppResponse);
  rpc CompleteAgentRun(CompleteAgentRunRequest) returns (CompleteAgentRunResponse);
  rpc CreateAppVersion(CreateAppVersionRequest) returns (CreateAppVersionResponse);
  rpc GetChatHistory(GetChatHistoryRequest) returns (GetChatHistoryResponse);
  rpc UpdateAppCodeGenType(UpdateAppCodeGenTypeRequest) returns (UpdateAppCodeGenTypeResponse);
  rpc GetAppDetail(GetAppDetailRequest) returns (GetAppDetailResponse);
  rpc GetUserInfo(GetUserInfoRequest) returns (GetUserInfoResponse);
}

message GetModelConfigRequest {
  int64 model_config_id = 1;
  int32 config_version = 2;
}

message GetModelConfigResponse {
  string provider = 1;
  string model_name = 2;
  string base_url = 3;
  string api_key = 4;
}

message BuildVueProjectRequest {
  int64 app_id = 1;
}

message BuildVueProjectResponse {
  string dist_path = 1;
  string install_log = 2;
  string build_log = 3;
  bool success = 4;
  string error_message = 5;
}

message DeployAppRequest {
  int64 app_id = 1;
  int64 user_id = 2;
}

message DeployAppResponse {
  string url = 1;
  bool success = 2;
  string error_message = 3;
}

message CompleteAgentRunRequest {
  int64 agent_run_id = 1;
  bool success = 2;
  string workspace_path = 3;
  int32 latency_ms = 4;
  string error_message = 5;
}

message CompleteAgentRunResponse {
  bool ok = 1;
}

message CreateAppVersionRequest {
  int64 app_id = 1;
  int64 agent_run_id = 2;
  string source_path = 3;
  string build_path = 4;
}

message CreateAppVersionResponse {
  int64 version_id = 1;
}

message ChatHistoryEntry {
  int64 id = 1;
  string role = 2;
  string content = 3;
  int64 created_at = 4;
}

message GetChatHistoryRequest {
  int64 session_id = 1;
  int32 limit = 2;
}

message GetChatHistoryResponse {
  repeated ChatHistoryEntry entries = 1;
}

message UpdateAppCodeGenTypeRequest {
  int64 app_id = 1;
  CodeGenType code_gen_type = 2;
}

message UpdateAppCodeGenTypeResponse {
  bool ok = 1;
}

message GetAppDetailRequest {
  int64 app_id = 1;
}

message GetAppDetailResponse {
  int64 id = 1;
  string name = 2;
  string description = 3;
  CodeGenType code_gen_type = 4;
  int64 user_id = 5;
  string created_at = 6;
  string updated_at = 7;
}

message GetUserInfoRequest {
  int64 user_id = 1;
}

message GetUserInfoResponse {
  int64 id = 1;
  string user_name = 2;
  string user_avatar = 3;
  string user_role = 4;
}
```

**Step 6: 提交 proto 文件**

```bash
git add proto/
git commit -m "feat: add gRPC proto definitions for Java-Python integration"
```

---

### Task 1.2: Java 端 gRPC 代码生成配置

**Files:**
- Modify: `backend-java/pom.xml`
- Create: `backend-java/src/main/java/com/adcage/acaicodefree/grpc/` (生成代码输出目录)

**Step 1: 在 pom.xml 中添加 gRPC 依赖和 protobuf-maven-plugin**

在 `<dependencies>` 中添加：

```xml
<dependency>
    <groupId>net.devh</groupId>
    <artifactId>grpc-spring-boot-starter</artifactId>
    <version>3.1.0.RELEASE</version>
</dependency>
<dependency>
    <groupId>io.grpc</groupId>
    <artifactId>grpc-protobuf</artifactId>
    <version>1.71.0</version>
</dependency>
<dependency>
    <groupId>io.grpc</groupId>
    <artifactId>grpc-stub</artifactId>
    <version>1.71.0</version>
</dependency>
<dependency>
    <groupId>org.apache.tomcat</groupId>
    <artifactId>annotations-api</artifactId>
    <version>6.0.53</version>
    <scope>provided</scope>
</dependency>
```

在 `<build><plugins>` 中添加 protobuf-maven-plugin：

```xml
<plugin>
    <groupId>org.xolstice.maven.plugins</groupId>
    <artifactId>protobuf-maven-plugin</artifactId>
    <version>0.6.1</version>
    <configuration>
        <protocArtifact>com.google.protobuf:protoc:3.25.5:exe:${os.detected.classifier}</protocArtifact>
        <pluginId>grpc-java</pluginId>
        <pluginArtifact>io.grpc:protoc-gen-grpc-java:1.71.0:exe:${os.detected.classifier}</pluginArtifact>
        <protoSourceRoot>${project.basedir}/../proto</protoSourceRoot>
    </configuration>
    <executions>
        <execution>
            <goals>
                <goal>compile</goal>
                <goal>compile-custom</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

**Step 2: 在 application.yml 中添加 gRPC 配置**

```yaml
grpc:
  server:
    port: 9090
  client:
    python-agent:
      address: 'static://localhost:9091'
      negotiationType: plaintext
```

**Step 3: 运行 protobuf 编译，验证代码生成**

```bash
cd backend-java && mvn compile
```

Expected: `target/generated-sources/protobuf/` 下生成 Java 类。

**Step 4: 提交**

```bash
git add backend-java/pom.xml backend-java/src/main/resources/application.yml
git commit -m "feat: add gRPC dependencies and protobuf code generation config"
```

---

### Task 1.3: Python 端 gRPC 代码生成配置

**Files:**
- Modify: `agent-runtime-python/pyproject.toml`
- Create: `agent-runtime-python/scripts/generate_grpc.py`
- Create: `agent-runtime-python/app/grpc/` (生成代码输出目录)

**Step 1: 在 pyproject.toml 中添加 gRPC 依赖**

```toml
dependencies = [
  # ... existing deps ...
  "grpcio>=1.68.0",
  "grpcio-tools>=1.68.0",
]
```

**Step 2: 创建代码生成脚本**

`scripts/generate_grpc.py`:
```python
import subprocess
import sys
from pathlib import Path

PROTO_DIR = Path(__file__).parent.parent.parent / "proto"
OUT_DIR = Path(__file__).parent.parent / "app" / "grpc"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    proto_files = list(PROTO_DIR.glob("*.proto"))
    if not proto_files:
        print("No .proto files found in", PROTO_DIR)
        sys.exit(1)
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        *[str(f) for f in proto_files],
    ]
    subprocess.check_call(cmd)
    print("Generated gRPC code in", OUT_DIR)

if __name__ == "__main__":
    main()
```

**Step 3: 运行代码生成**

```bash
cd agent-runtime-python && pip install -e ".[dev]" && python scripts/generate_grpc.py
```

Expected: `app/grpc/` 下生成 `_pb2.py` 和 `_pb2_grpc.py` 文件。

**Step 4: 提交**

```bash
git add agent-runtime-python/pyproject.toml agent-runtime-python/scripts/ agent-runtime-python/app/grpc/
git commit -m "feat: add gRPC dependencies and code generation for Python"
```

---

## Phase 2: Java gRPC Server（ToolService + PlatformService）

### Task 2.1: ToolService gRPC Server 实现

**Files:**
- Create: `backend-java/src/main/java/com/adcage/acaicodefree/grpc/server/GrpcToolService.java`

**Step 1: 实现 GrpcToolService**

该类将 Java 端已有的 `FileReadTool`、`FileWriteTool`、`FileModifyTool`、`FileDeleteTool`、`FileDirReadTool` 的逻辑封装为 gRPC 服务。

```java
package com.adcage.acaicodefree.grpc.server;

import com.adcage.acaicodefree.grpc.common.CodeGenType;
import com.adcage.acaicodefree.grpc.tool.*;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import io.grpc.stub.StreamObserver;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;

import com.adcage.acaicodefree.ai.tools.FileReadTool;
import com.adcage.acaicodefree.ai.tools.FileWriteTool;
import com.adcage.acaicodefree.ai.tools.FileModifyTool;
import com.adcage.acaicodefree.ai.tools.FileDeleteTool;
import com.adcage.acaicodefree.ai.tools.FileDirReadTool;
import jakarta.annotation.Resource;

@Slf4j
@GrpcService
public class GrpcToolService extends ToolServiceGrpc.ToolServiceImplBase {

    @Resource
    private FileReadTool fileReadTool;
    @Resource
    private FileWriteTool fileWriteTool;
    @Resource
    private FileModifyTool fileModifyTool;
    @Resource
    private FileDeleteTool fileDeleteTool;
    @Resource
    private FileDirReadTool fileDirReadTool;

    @Override
    public void readFile(ReadFileRequest request, StreamObserver<ReadFileResponse> responseObserver) {
        try {
            String content = fileReadTool.readFile(
                    request.getRelativePath(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
            );
            responseObserver.onNext(ReadFileResponse.newBuilder().setContent(content).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC readFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void writeFile(WriteFileRequest request, StreamObserver<WriteFileResponse> responseObserver) {
        try {
            String message = fileWriteTool.writeFile(
                    request.getRelativePath(),
                    request.getContent(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
            );
            responseObserver.onNext(WriteFileResponse.newBuilder().setMessage(message).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC writeFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void modifyFile(ModifyFileRequest request, StreamObserver<ModifyFileResponse> responseObserver) {
        try {
            String message = fileModifyTool.modifyFile(
                    request.getRelativePath(),
                    request.getOldContent(),
                    request.getNewContent(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
            );
            responseObserver.onNext(ModifyFileResponse.newBuilder().setMessage(message).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC modifyFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void deleteFile(DeleteFileRequest request, StreamObserver<DeleteFileResponse> responseObserver) {
        try {
            String message = fileDeleteTool.deleteFile(
                    request.getRelativePath(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
            );
            responseObserver.onNext(DeleteFileResponse.newBuilder().setMessage(message).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC deleteFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void readDir(ReadDirRequest request, StreamObserver<ReadDirResponse> responseObserver) {
        try {
            String entries = fileDirReadTool.readDir(
                    request.getRelativePath(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
            );
            responseObserver.onNext(ReadDirResponse.newBuilder().setEntries(entries).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC readDir failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public StreamObserver<WriteFileRequest> streamWriteFiles(StreamObserver<BatchWriteResponse> responseObserver) {
        StringBuilder messages = new StringBuilder();
        int[] counts = {0, 0};
        return new StreamObserver<>() {
            @Override
            public void onNext(WriteFileRequest request) {
                try {
                    String message = fileWriteTool.writeFile(
                            request.getRelativePath(),
                            request.getContent(),
                            request.getAppId(),
                            mapCodeGenType(request.getCodeGenType())
                    );
                    counts[0]++;
                    messages.append(message).append("\n");
                } catch (Exception e) {
                    counts[1]++;
                    messages.append("失败: ").append(e.getMessage()).append("\n");
                    log.warn("streamWriteFiles item failed", e);
                }
            }

            @Override
            public void onError(Throwable t) {
                log.error("streamWriteFiles client error", t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onNext(BatchWriteResponse.newBuilder()
                        .setSuccessCount(counts[0])
                        .setFailureCount(counts[1])
                        .addMessages(messages.toString().trim())
                        .build());
                responseObserver.onCompleted();
            }
        };
    }

    private CodeGenTypeEnum mapCodeGenType(CodeGenType grpcType) {
        return switch (grpcType) {
            case SINGLE_FILE -> CodeGenTypeEnum.SINGLE_FILE;
            case MULTI_FILE -> CodeGenTypeEnum.MULTI_FILE;
            case VUE_PROJECT -> CodeGenTypeEnum.VUE_PROJECT;
            default -> CodeGenTypeEnum.VUE_PROJECT;
        };
    }
}
```

**Step 2: 编译验证**

```bash
cd backend-java && mvn compile
```

Expected: 编译成功，无错误。

**Step 3: 提交**

```bash
git add backend-java/src/main/java/com/adcage/acaicodefree/grpc/server/GrpcToolService.java
git commit -m "feat: implement gRPC ToolService server wrapping existing file tools"
```

---

### Task 2.2: PlatformService gRPC Server 实现

**Files:**
- Create: `backend-java/src/main/java/com/adcage/acaicodefree/grpc/server/GrpcPlatformService.java`

**Step 1: 实现 GrpcPlatformService**

该类封装 Java 端的平台能力：模型配置查询、构建部署、AgentRun 管理、聊天历史、应用/用户信息。

```java
package com.adcage.acaicodefree.grpc.server;

import com.adcage.acaicodefree.grpc.common.CodeGenType;
import com.adcage.acaicodefree.grpc.platform.*;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.model.vo.ModelConfigRuntimeVO;
import com.adcage.acaicodefree.service.*;
import com.adcage.acaicodefree.core.build.VueProjectBuildService;
import io.grpc.stub.StreamObserver;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;
import jakarta.annotation.Resource;

@Slf4j
@GrpcService
public class GrpcPlatformService extends PlatformServiceGrpc.PlatformServiceImplBase {

    @Resource
    private ModelConfigService modelConfigService;
    @Resource
    private AgentRunService agentRunService;
    @Resource
    private AppVersionService appVersionService;
    @Resource
    private AppService appService;
    @Resource
    private UserService userService;
    @Resource
    private VueProjectBuildService vueProjectBuildService;

    @Override
    public void getModelConfig(GetModelConfigRequest request, StreamObserver<GetModelConfigResponse> responseObserver) {
        try {
            ModelConfigRuntimeVO config = modelConfigService.getRuntimeConfig(
                    request.getModelConfigId(),
                    request.getConfigVersion()
            );
            responseObserver.onNext(GetModelConfigResponse.newBuilder()
                    .setProvider(config.getProvider())
                    .setModelName(config.getModelName())
                    .setBaseUrl(config.getBaseUrl())
                    .setApiKey(config.getApiKey())
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC getModelConfig failed", e);
            responseObserver.onError(io.grpc.Status.NOT_FOUND
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void buildVueProject(BuildVueProjectRequest request, StreamObserver<BuildVueProjectResponse> responseObserver) {
        try {
            var result = vueProjectBuildService.buildVueProject(request.getAppId());
            BuildVueProjectResponse.Builder builder = BuildVueProjectResponse.newBuilder()
                    .setSuccess(true)
                    .setDistPath(result.getDistPath() != null ? result.getDistPath() : "")
                    .setInstallLog(result.getInstallLog() != null ? result.getInstallLog() : "")
                    .setBuildLog(result.getBuildLog() != null ? result.getBuildLog() : "");
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC buildVueProject failed", e);
            responseObserver.onNext(BuildVueProjectResponse.newBuilder()
                    .setSuccess(false)
                    .setErrorMessage(e.getMessage() != null ? e.getMessage() : "unknown error")
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void deployApp(DeployAppRequest request, StreamObserver<DeployAppResponse> responseObserver) {
        try {
            User user = userService.getById(request.getUserId());
            String url = appService.deployApp(request.getAppId(), user);
            responseObserver.onNext(DeployAppResponse.newBuilder()
                    .setSuccess(true)
                    .setUrl(url != null ? url : "")
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC deployApp failed", e);
            responseObserver.onNext(DeployAppResponse.newBuilder()
                    .setSuccess(false)
                    .setErrorMessage(e.getMessage() != null ? e.getMessage() : "unknown error")
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void completeAgentRun(CompleteAgentRunRequest request, StreamObserver<CompleteAgentRunResponse> responseObserver) {
        try {
            if (request.getSuccess()) {
                agentRunService.completeAgentRun(
                        request.getAgentRunId(),
                        request.getWorkspacePath(),
                        request.getLatencyMs()
                );
            } else {
                agentRunService.failAgentRun(
                        request.getAgentRunId(),
                        request.getErrorMessage()
                );
            }
            responseObserver.onNext(CompleteAgentRunResponse.newBuilder().setOk(true).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC completeAgentRun failed", e);
            responseObserver.onNext(CompleteAgentRunResponse.newBuilder().setOk(false).build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void createAppVersion(CreateAppVersionRequest request, StreamObserver<CreateAppVersionResponse> responseObserver) {
        try {
            Long versionId = appVersionService.createAppVersion(
                    request.getAppId(),
                    request.getAgentRunId(),
                    request.getSourcePath(),
                    request.getBuildPath()
            );
            responseObserver.onNext(CreateAppVersionResponse.newBuilder()
                    .setVersionId(versionId != null ? versionId : 0L)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC createAppVersion failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void getChatHistory(GetChatHistoryRequest request, StreamObserver<GetChatHistoryResponse> responseObserver) {
        try {
            var query = new com.adcage.acaicodefree.model.dto.chat.ChatHistoryQueryRequest();
            query.setSessionId(request.getSessionId());
            query.setPageSize(request.getLimit() > 0 ? request.getLimit() : 50);
            query.setCurrent(1);
            var user = new User();
            user.setId(0L);
            user.setUserRole("admin");
            var page = appService.listChatHistoryByPage(query, user);
            var builder = GetChatHistoryResponse.newBuilder();
            page.getRecords().forEach(record -> {
                ChatHistoryEntry entry = ChatHistoryEntry.newBuilder()
                        .setId(record.getId() != null ? record.getId() : 0L)
                        .setRole(record.getRole() != null ? record.getRole() : "")
                        .setContent(record.getContent() != null ? record.getContent() : "")
                        .build();
                builder.addEntries(entry);
            });
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC getChatHistory failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void updateAppCodeGenType(UpdateAppCodeGenTypeRequest request, StreamObserver<UpdateAppCodeGenTypeResponse> responseObserver) {
        try {
            App app = appService.getById(request.getAppId());
            app.setCodeGenType(mapCodeGenType(request.getCodeGenType()).getValue());
            appService.updateById(app);
            responseObserver.onNext(UpdateAppCodeGenTypeResponse.newBuilder().setOk(true).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC updateAppCodeGenType failed", e);
            responseObserver.onNext(UpdateAppCodeGenTypeResponse.newBuilder().setOk(false).build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void getAppDetail(GetAppDetailRequest request, StreamObserver<GetAppDetailResponse> responseObserver) {
        try {
            App app = appService.getById(request.getAppId());
            if (app == null) {
                responseObserver.onError(io.grpc.Status.NOT_FOUND
                        .withDescription("App not found: " + request.getAppId()).asRuntimeException());
                return;
            }
            responseObserver.onNext(GetAppDetailResponse.newBuilder()
                    .setId(app.getId())
                    .setName(app.getAppName() != null ? app.getAppName() : "")
                    .setDescription(app.getDescription() != null ? app.getDescription() : "")
                    .setCodeGenType(mapJavaCodeGenType(app.getCodeGenType()))
                    .setUserId(app.getUserId() != null ? app.getUserId() : 0L)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC getAppDetail failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void getUserInfo(GetUserInfoRequest request, StreamObserver<GetUserInfoResponse> responseObserver) {
        try {
            User user = userService.getById(request.getUserId());
            if (user == null) {
                responseObserver.onError(io.grpc.Status.NOT_FOUND
                        .withDescription("User not found: " + request.getUserId()).asRuntimeException());
                return;
            }
            responseObserver.onNext(GetUserInfoResponse.newBuilder()
                    .setId(user.getId())
                    .setUserName(user.getUserName() != null ? user.getUserName() : "")
                    .setUserAvatar(user.getUserAvatar() != null ? user.getUserAvatar() : "")
                    .setUserRole(user.getUserRole() != null ? user.getUserRole() : "")
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC getUserInfo failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    private CodeGenTypeEnum mapCodeGenType(CodeGenType grpcType) {
        return switch (grpcType) {
            case SINGLE_FILE -> CodeGenTypeEnum.SINGLE_FILE;
            case MULTI_FILE -> CodeGenTypeEnum.MULTI_FILE;
            case VUE_PROJECT -> CodeGenTypeEnum.VUE_PROJECT;
            default -> CodeGenTypeEnum.VUE_PROJECT;
        };
    }

    private CodeGenType mapJavaCodeGenType(String javaType) {
        if (javaType == null) return CodeGenType.VUE_PROJECT;
        return switch (javaType) {
            case "single_file" -> CodeGenType.SINGLE_FILE;
            case "multi-file" -> CodeGenType.MULTI_FILE;
            case "vue_project" -> CodeGenType.VUE_PROJECT;
            default -> CodeGenType.VUE_PROJECT;
        };
    }
}
```

**Step 2: 编译验证**

```bash
cd backend-java && mvn compile
```

**Step 3: 提交**

```bash
git add backend-java/src/main/java/com/adcage/acaicodefree/grpc/server/GrpcPlatformService.java
git commit -m "feat: implement gRPC PlatformService server for platform capabilities"
```

---

### Task 2.3: gRPC 服务端内部认证拦截器

**Files:**
- Create: `backend-java/src/main/java/com/adcage/acaicodefree/grpc/server/GrpcInternalAuthInterceptor.java`

**Step 1: 实现内部认证拦截器**

防止未授权的外部客户端调用 Java 的 gRPC 服务。使用与现有 HTTP 内部接口相同的 `X-Internal-Secret` 机制。

```java
package com.adcage.acaicodefree.grpc.server;

import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import net.devh.boot.grpc.server.interceptor.GrpcGlobalServerInterceptor;
import org.springframework.beans.factory.annotation.Value;

@GrpcGlobalServerInterceptor
public class GrpcInternalAuthInterceptor implements ServerInterceptor {

    private static final Metadata.Key<String> INTERNAL_SECRET_KEY =
            Metadata.Key.of("x-internal-secret", Metadata.ASCII_STRING_MARSHALLER);

    @Value("${agent.runtime-internal-secret:}")
    private String internalSecret;

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers,
            ServerCallHandler<ReqT, RespT> next) {
        if (internalSecret != null && !internalSecret.isBlank()) {
            String provided = headers.get(INTERNAL_SECRET_KEY);
            if (!internalSecret.equals(provided)) {
                call.close(io.grpc.Status.UNAUTHENTICATED
                        .withDescription("Invalid internal secret"), headers);
                return new ServerCall.Listener<>() {};
            }
        }
        return next.startCall(call, headers);
    }
}
```

**Step 2: 编译验证**

```bash
cd backend-java && mvn compile
```

**Step 3: 提交**

```bash
git add backend-java/src/main/java/com/adcage/acaicodefree/grpc/server/GrpcInternalAuthInterceptor.java
git commit -m "feat: add gRPC server auth interceptor with internal secret"
```

---

## Phase 3: Python gRPC Server（CodeGenerationService）

### Task 3.1: Python gRPC Server 实现

**Files:**
- Create: `agent-runtime-python/app/grpc_server/server.py`
- Create: `agent-runtime-python/app/grpc_server/code_generation_servicer.py`
- Modify: `agent-runtime-python/app/main.py` — 添加 gRPC server 启动

**Step 1: 创建 CodeGenerationService Servicer**

`app/grpc_server/code_generation_servicer.py`：

将现有的 `AgentService.stream()` 输出的 `AgentEvent` 转换为 gRPC 的 `CodeGenerationEvent`。核心改造是将 Python 端的 `AgentEvent(eventType: str, data: dict)` 泛型事件替换为 proto 定义的有类型 `CodeGenerationEvent`。

```python
import grpc
from grpc import aio
import logging

from app.grpc import code_generation_pb2
from app.grpc import code_generation_pb2_grpc
from app.grpc import common_pb2
from app.services.agent_service import AgentService
from app.services.chat_model_factory import ChatModelFactory
from app.services.model_config_client import ModelConfigClient
from app.services.prompt_builder import PromptBuilder
from app.schemas.code_generation import CodeGenerationRequest as PyCodeGenRequest

logger = logging.getLogger("app.grpc_server.code_generation_servicer")


def _map_event_type(event_type: str) -> int:
    mapping = {
        "agent_start": common_pb2.AGENT_START,
        "ai_response": common_pb2.AI_RESPONSE,
        "tool_request": common_pb2.TOOL_REQUEST,
        "tool_executed": common_pb2.TOOL_EXECUTED,
        "error": common_pb2.ERROR,
        "done": common_pb2.DONE,
    }
    return mapping.get(event_type, common_pb2.EVENT_TYPE_UNSPECIFIED)


def _map_code_gen_type(code_gen_type: str) -> int:
    mapping = {
        "single_file": common_pb2.SINGLE_FILE,
        "multi-file": common_pb2.MULTI_FILE,
        "vue_project": common_pb2.VUE_PROJECT,
    }
    return mapping.get(code_gen_type, common_pb2.VUE_PROJECT)


def _build_grpc_event(event) -> code_generation_pb2.CodeGenerationEvent:
    builder = code_generation_pb2.CodeGenerationEvent(
        agent_run_id=event.agentRunId,
        seq=event.seq,
        event_type=_map_event_type(event.eventType),
    )
    data = event.data

    if event.eventType == "ai_response":
        text = data.get("text", data.get("content", ""))
        builder.ai_response.CopyFrom(common_pb2.AiResponseData(
            text=text,
            fallback=data.get("fallback", False),
        ))
    elif event.eventType == "tool_request":
        builder.tool_request.CopyFrom(common_pb2.ToolRequestData(
            id=data.get("id", "unknown"),
            name=data.get("name", "unknown"),
            arguments=data.get("arguments", "{}") if isinstance(data.get("arguments"), str) else str(data.get("arguments", "{}")),
        ))
    elif event.eventType == "tool_executed":
        builder.tool_executed.CopyFrom(common_pb2.ToolExecutedData(
            id=data.get("id", "unknown"),
            name=data.get("name", "unknown"),
            arguments=data.get("arguments", "{}") if isinstance(data.get("arguments"), str) else str(data.get("arguments", "{}")),
            result=data.get("result", ""),
        ))
    elif event.eventType == "error":
        builder.error.CopyFrom(common_pb2.ErrorData(
            message=data.get("message", "unknown error"),
        ))
    elif event.eventType == "done":
        builder.done.CopyFrom(common_pb2.DoneData(
            message=data.get("message", ""),
        ))
    elif event.eventType == "agent_start":
        builder.ai_response.CopyFrom(common_pb2.AiResponseData(
            text="Agent started",
        ))

    return builder


class CodeGenerationServicer(code_generation_pb2_grpc.CodeGenerationServiceServicer):

    def __init__(self, agent_service: AgentService):
        self._agent_service = agent_service

    async def StreamGenerate(self, request, context):
        py_request = PyCodeGenRequest(
            agentRunId=request.agent_run_id,
            appId=request.app_id,
            sessionId=request.session_id,
            userId=request.user_id,
            prompt=request.prompt,
            codeGenType=common_pb2.CodeGenType.Name(request.code_gen_type).lower().replace("code_gen_type_", ""),
            workspacePath=request.workspace_path or None,
            modelConfigId=request.model_config_id or None,
            configVersion=request.config_version or None,
        )
        try:
            async for event in self._agent_service.stream(py_request):
                grpc_event = _build_grpc_event(event)
                yield grpc_event
        except Exception as e:
            logger.error("StreamGenerate failed: %s", e, exc_info=True)
            yield code_generation_pb2.CodeGenerationEvent(
                agent_run_id=request.agent_run_id,
                seq=0,
                event_type=common_pb2.ERROR,
                error=common_pb2.ErrorData(message=str(e)),
            )

    async def StreamModify(self, request, context):
        py_request = PyCodeGenRequest(
            agentRunId=request.agent_run_id,
            appId=request.app_id,
            sessionId=request.session_id,
            userId=request.user_id,
            prompt=request.prompt,
            codeGenType=common_pb2.CodeGenType.Name(request.code_gen_type).lower().replace("code_gen_type_", ""),
            workspacePath=request.workspace_path or None,
            modelConfigId=request.model_config_id or None,
            configVersion=request.config_version or None,
        )
        try:
            async for event in self._agent_service.stream(py_request):
                grpc_event = _build_grpc_event(event)
                yield grpc_event
        except Exception as e:
            logger.error("StreamModify failed: %s", e, exc_info=True)
            yield code_generation_pb2.CodeGenerationEvent(
                agent_run_id=request.agent_run_id,
                seq=0,
                event_type=common_pb2.ERROR,
                error=common_pb2.ErrorData(message=str(e)),
            )

    async def RouteCodeGenType(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("RouteCodeGenType not yet implemented")
        await context.abort()

    async def ValidatePrompt(self, request, context):
        prompt = request.prompt
        if not prompt or len(prompt.strip()) == 0:
            return code_generation_pb2.ValidatePromptResponse(valid=False, reason="提示词不能为空")
        if len(prompt) > 2000:
            return code_generation_pb2.ValidatePromptResponse(valid=False, reason="提示词长度不能超过2000字")
        injection_keywords = ["ignore previous instructions", "bypass", "jailbreak"]
        lower = prompt.lower()
        for kw in injection_keywords:
            if kw in lower:
                return code_generation_pb2.ValidatePromptResponse(valid=False, reason=f"提示词包含不允许的内容")
        return code_generation_pb2.ValidatePromptResponse(valid=True)
```

**Step 2: 创建 gRPC server 启动模块**

`app/grpc_server/server.py`：

```python
import logging
from concurrent import futures

import grpc
from grpc import aio

from app.core.config import settings
from app.grpc import code_generation_pb2_grpc
from app.grpc_server.code_generation_servicer import CodeGenerationServicer
from app.services.agent_service import AgentService
from app.services.chat_model_factory import ChatModelFactory
from app.services.model_config_client import ModelConfigClient
from app.services.prompt_builder import PromptBuilder

logger = logging.getLogger("app.grpc_server")


async def create_grpc_server() -> aio.Server:
    model_config_client = ModelConfigClient(settings.java_platform_base_url, settings.agent_internal_secret)
    chat_model_factory = ChatModelFactory()
    prompt_builder = PromptBuilder()
    agent_service = AgentService(model_config_client, chat_model_factory, prompt_builder)

    servicer = CodeGenerationServicer(agent_service)

    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))
    code_generation_pb2_grpc.add_CodeGenerationServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{settings.grpc_server_port}")
    logger.info("gRPC server listening on port %s", settings.grpc_server_port)
    return server
```

**Step 3: 在 config.py 中添加 gRPC 端口配置**

在 `Settings` 类中添加：

```python
grpc_server_port: int = 9091
```

**Step 4: 修改 main.py，添加 gRPC server 生命周期管理**

在 FastAPI 的 lifespan 中启动和停止 gRPC server：

```python
from contextlib import asynccontextmanager
from app.grpc_server.server import create_grpc_server

@asynccontextmanager
async def lifespan(app: FastAPI):
    grpc_server = await create_grpc_server()
    await grpc_server.start()
    logger.info("gRPC server started")
    yield
    await grpc_server.stop(grace=5)
    logger.info("gRPC server stopped")
```

将 `create_app()` 中的 FastAPI 实例化改为使用 `lifespan`。

**Step 5: 验证启动**

```bash
cd agent-runtime-python && python -m uvicorn app.main:app --port 9000
```

Expected: 日志中出现 "gRPC server listening on port 9091"。

**Step 6: 提交**

```bash
git add agent-runtime-python/app/grpc_server/ agent-runtime-python/app/main.py agent-runtime-python/app/core/config.py
git commit -m "feat: implement Python gRPC server for CodeGenerationService"
```

---

## Phase 4: Java gRPC Client（替代 PythonAgentRuntime）

### Task 4.1: 实现新的 GrpcPythonAgentRuntime

**Files:**
- Create: `backend-java/src/main/java/com/adcage/acaicodefree/grpc/client/GrpcPythonAgentRuntime.java`
- Modify: `backend-java/src/main/java/com/adcage/acaicodefree/runtime/impl/PythonAgentRuntime.java` — 标记 @Deprecated

**Step 1: 实现 GrpcPythonAgentRuntime**

替代旧的 `PythonAgentRuntime`（HTTP+SSE），通过 gRPC Server Streaming 调用 Python 的 `CodeGenerationService.StreamGenerate`。返回强类型的 `CodeGenerationEvent` 流，然后转换为 Java 端的 `StreamMessage` JSON。

```java
package com.adcage.acaicodefree.grpc.client;

import com.adcage.acaicodefree.grpc.codegen.*;
import com.adcage.acaicodefree.grpc.common.*;
import com.adcage.acaicodefree.ai.model.message.AiResponseMessage;
import com.adcage.acaicodefree.ai.model.message.StreamMessage;
import com.adcage.acaicodefree.ai.model.message.ToolRequestMessage;
import com.adcage.acaicodefree.ai.model.message.ToolExecutedMessage;
import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import cn.hutool.json.JSONUtil;
import io.grpc.stub.StreamObserver;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

import java.util.concurrent.atomic.AtomicLong;

@Slf4j
@Component
public class GrpcPythonAgentRuntime implements CodeGenerationRuntime {

    private static final String NAME = "python-agent";

    @GrpcClient("python-agent")
    private CodeGenerationServiceGrpc.CodeGenerationServiceStub codeGenServiceStub;

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        Sinks.Many<String> sink = Sinks.many().unicast().onBackpressureBuffer();

        CodeGenerationRequest grpcRequest = buildGrpcRequest(request);

        codeGenServiceStub.streamGenerate(grpcRequest, new StreamObserver<>() {
            @Override
            public void onNext(CodeGenerationEvent event) {
                String json = mapEventToStreamMessageJson(event);
                if (json != null) {
                    sink.tryEmitNext(json);
                }
            }

            @Override
            public void onError(Throwable t) {
                log.error("gRPC StreamGenerate error: {}", t.getMessage(), t);
                sink.tryEmitNext(JSONUtil.toJsonStr(new AiResponseMessage("生成失败：" + t.getMessage())));
                sink.tryEmitComplete();
            }

            @Override
            public void onCompleted() {
                sink.tryEmitComplete();
            }
        });

        return sink.asFlux();
    }

    private CodeGenerationRequest buildGrpcRequest(CodeGenerationRequest request) {
        CodeGenerationRequest.Builder builder = CodeGenerationRequest.newBuilder()
                .setAgentRunId(String.valueOf(request.getAgentRunId()))
                .setAppId(request.getAppId() != null ? request.getAppId() : 0L)
                .setSessionId(request.getSessionId() != null ? request.getSessionId() : 0L)
                .setUserId(request.getLoginUser() != null ? request.getLoginUser().getId() : 0L)
                .setPrompt(request.getMessage() != null ? request.getMessage() : "")
                .setWorkspacePath(request.getWorkspacePath() != null ? request.getWorkspacePath() : "")
                .setModelConfigId(request.getModelConfigId() != null ? request.getModelConfigId() : 0L)
                .setConfigVersion(request.getConfigVersion() != null ? request.getConfigVersion() : 0);

        if (request.getCodeGenTypeEnum() != null) {
            builder.setCodeGenType(mapJavaCodeGenType(request.getCodeGenTypeEnum()));
        }
        if (request.getApp() != null && request.getApp().getCodeGenType() != null) {
            builder.setCodeGenType(mapJavaCodeGenTypeStr(request.getApp().getCodeGenType()));
        }

        return builder.build();
    }

    private CodeGenType mapJavaCodeGenType(com.adcage.acaicodefree.model.enums.CodeGenTypeEnum type) {
        return switch (type) {
            case SINGLE_FILE -> CodeGenType.SINGLE_FILE;
            case MULTI_FILE -> CodeGenType.MULTI_FILE;
            case VUE_PROJECT -> CodeGenType.VUE_PROJECT;
        };
    }

    private CodeGenType mapJavaCodeGenTypeStr(String type) {
        if (type == null) return CodeGenType.VUE_PROJECT;
        return switch (type) {
            case "single_file" -> CodeGenType.SINGLE_FILE;
            case "multi-file" -> CodeGenType.MULTI_FILE;
            case "vue_project" -> CodeGenType.VUE_PROJECT;
            default -> CodeGenType.VUE_PROJECT;
        };
    }

    private String mapEventToStreamMessageJson(CodeGenerationEvent event) {
        switch (event.getEventType()) {
            case AI_RESPONSE:
                return JSONUtil.toJsonStr(new AiResponseMessage(event.getAiResponse().getText()));
            case TOOL_REQUEST:
                ToolRequestData req = event.getToolRequest();
                return JSONUtil.toJsonStr(new ToolRequestMessage(req.getId(), req.getName(), req.getArguments()));
            case TOOL_EXECUTED:
                ToolExecutedData exec = event.getToolExecuted();
                return JSONUtil.toJsonStr(new ToolExecutedMessage(exec.getId(), exec.getName(), exec.getArguments(), exec.getResult()));
            case ERROR:
                return JSONUtil.toJsonStr(new AiResponseMessage("生成失败：" + event.getError().getMessage()));
            case DONE:
                return JSONUtil.toJsonStr(new AiResponseMessage(event.getDone().getMessage()));
            case AGENT_START:
                return null;
            default:
                return null;
        }
    }
}
```

**Step 2: 标记旧 PythonAgentRuntime 为 @Deprecated**

在 `PythonAgentRuntime.java` 类上添加 `@Deprecated` 注解，并注释掉 `@Component` 以避免 Bean 冲突。

**Step 3: 删除 PythonAgentEventMapper**

不再需要手动映射泛型 dict 事件，`GrpcPythonAgentRuntime` 直接消费强类型 proto 事件。

**Step 4: 编译验证**

```bash
cd backend-java && mvn compile
```

**Step 5: 提交**

```bash
git add backend-java/src/main/java/com/adcage/acaicodefree/grpc/client/
git add backend-java/src/main/java/com/adcage/acaicodefree/runtime/impl/PythonAgentRuntime.java
git add backend-java/src/main/java/com/adcage/acaicodefree/runtime/PythonAgentEventMapper.java
git commit -m "feat: implement GrpcPythonAgentRuntime replacing HTTP+SSE with gRPC streaming"
```

---

### Task 4.2: 统一流处理，消除 AppServiceImpl 分支

**Files:**
- Modify: `backend-java/src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`

**Step 1: 统一流处理逻辑**

当前 `AppServiceImpl.chatToGenCode()` 中有分支：
```java
if ("java-agent".equals(runtime.getName())) {
    handledStream = streamHandlerExecutor.handle(...);
} else {
    handledStream = sourceStream.doOnNext(chunk -> ...);
}
```

改造后，`GrpcPythonAgentRuntime` 返回的 `Flux<String>` 格式与 `JavaAgentRuntime` 完全一致（都是 `StreamMessage` 的 JSON），因此可以统一走 `streamHandlerExecutor.handle()`，删除分支。

```java
handledStream = streamHandlerExecutor.handle(codeGenTypeEnum, sourceStream, readableAssistantMessageBuilder);
```

**Step 2: 编译验证**

```bash
cd backend-java && mvn compile
```

**Step 3: 提交**

```bash
git add backend-java/src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java
git commit -m "feat: unify stream processing for Java and Python agent runtimes"
```

---

## Phase 5: Python gRPC Client（替代 ModelConfigClient + FileTools）

### Task 5.1: Python gRPC Client 基础设施

**Files:**
- Create: `agent-runtime-python/app/grpc_client/__init__.py`
- Create: `agent-runtime-python/app/grpc_client/channel.py`
- Create: `agent-runtime-python/app/grpc_client/tool_client.py`
- Create: `agent-runtime-python/app/grpc_client/platform_client.py`

**Step 1: 创建 gRPC channel 管理**

`app/grpc_client/channel.py`：

```python
import grpc
from grpc import aio
from app.core.config import settings

_channel: aio.Channel | None = None


async def get_channel() -> aio.Channel:
    global _channel
    if _channel is None:
        options = []
        if settings.agent_internal_secret:
            options.append(("grpc.default_authority", settings.agent_internal_secret))

        _channel = aio.insecure_channel(
            settings.java_grpc_target,
            options=options,
        )
    return _channel


async def close_channel():
    global _channel
    if _channel is not None:
        await _channel.close()
        _channel = None
```

**Step 2: 在 config.py 中添加 Java gRPC 地址**

```python
java_grpc_target: str = "localhost:9090"
```

**Step 3: 创建 ToolService gRPC Client**

`app/grpc_client/tool_client.py`：

封装对 Java 端 `ToolService` 的远程调用，替代本地的 `FileTools`。

```python
import grpc
from grpc import aio
import logging

from app.grpc import tool_service_pb2
from app.grpc import tool_service_pb2_grpc
from app.grpc import common_pb2
from app.grpc_client.channel import get_channel

logger = logging.getLogger("app.grpc_client.tool_client")


def _map_code_gen_type(code_gen_type: str) -> int:
    mapping = {
        "single_file": common_pb2.SINGLE_FILE,
        "multi-file": common_pb2.MULTI_FILE,
        "vue_project": common_pb2.VUE_PROJECT,
    }
    return mapping.get(code_gen_type, common_pb2.VUE_PROJECT)


class GrpcToolClient:

    def __init__(self, app_id: int, code_gen_type: str):
        self._app_id = app_id
        self._code_gen_type = code_gen_type
        self._stub = None

    async def _get_stub(self) -> tool_service_pb2_grpc.ToolServiceStub:
        if self._stub is None:
            channel = await get_channel()
            self._stub = tool_service_pb2_grpc.ToolServiceStub(channel)
        return self._stub

    async def read_file(self, relative_path: str) -> str:
        stub = await self._get_stub()
        request = tool_service_pb2.ReadFileRequest(
            app_id=self._app_id,
            code_gen_type=_map_code_gen_type(self._code_gen_type),
            relative_path=relative_path,
        )
        response = await stub.ReadFile(request)
        return response.content

    async def write_file(self, relative_path: str, content: str) -> str:
        stub = await self._get_stub()
        request = tool_service_pb2.WriteFileRequest(
            app_id=self._app_id,
            code_gen_type=_map_code_gen_type(self._code_gen_type),
            relative_path=relative_path,
            content=content,
        )
        response = await stub.WriteFile(request)
        return response.message

    async def modify_file(self, relative_path: str, old_content: str, new_content: str) -> str:
        stub = await self._get_stub()
        request = tool_service_pb2.ModifyFileRequest(
            app_id=self._app_id,
            code_gen_type=_map_code_gen_type(self._code_gen_type),
            relative_path=relative_path,
            old_content=old_content,
            new_content=new_content,
        )
        response = await stub.ModifyFile(request)
        return response.message

    async def delete_file(self, relative_path: str) -> str:
        stub = await self._get_stub()
        request = tool_service_pb2.DeleteFileRequest(
            app_id=self._app_id,
            code_gen_type=_map_code_gen_type(self._code_gen_type),
            relative_path=relative_path,
        )
        response = await stub.DeleteFile(request)
        return response.message

    async def read_dir(self, relative_path: str = ".") -> str:
        stub = await self._get_stub()
        request = tool_service_pb2.ReadDirRequest(
            app_id=self._app_id,
            code_gen_type=_map_code_gen_type(self._code_gen_type),
            relative_path=relative_path,
        )
        response = await stub.ReadDir(request)
        return response.entries
```

**Step 4: 创建 PlatformService gRPC Client**

`app/grpc_client/platform_client.py`：

```python
from grpc import aio
import logging

from app.grpc import platform_service_pb2
from app.grpc import platform_service_pb2_grpc
from app.grpc_client.channel import get_channel

logger = logging.getLogger("app.grpc_client.platform_client")


class GrpcPlatformClient:

    def __init__(self):
        self._stub = None

    async def _get_stub(self) -> platform_service_pb2_grpc.PlatformServiceStub:
        if self._stub is None:
            channel = await get_channel()
            self._stub = platform_service_pb2_grpc.PlatformServiceStub(channel)
        return self._stub

    async def get_model_config(self, model_config_id: int, config_version: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.GetModelConfigRequest(
            model_config_id=model_config_id,
            config_version=config_version,
        )
        response = await stub.GetModelConfig(request)
        return {
            "provider": response.provider,
            "modelName": response.model_name,
            "baseUrl": response.base_url,
            "apiKey": response.api_key,
        }

    async def build_vue_project(self, app_id: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.BuildVueProjectRequest(app_id=app_id)
        response = await stub.BuildVueProject(request)
        return {
            "success": response.success,
            "distPath": response.dist_path,
            "installLog": response.install_log,
            "buildLog": response.build_log,
            "errorMessage": response.error_message,
        }

    async def deploy_app(self, app_id: int, user_id: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.DeployAppRequest(app_id=app_id, user_id=user_id)
        response = await stub.DeployApp(request)
        return {"success": response.success, "url": response.url, "errorMessage": response.error_message}

    async def complete_agent_run(self, agent_run_id: int, success: bool, workspace_path: str = "", latency_ms: int = 0, error_message: str = "") -> bool:
        stub = await self._get_stub()
        request = platform_service_pb2.CompleteAgentRunRequest(
            agent_run_id=agent_run_id,
            success=success,
            workspace_path=workspace_path,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        response = await stub.CompleteAgentRun(request)
        return response.ok

    async def create_app_version(self, app_id: int, agent_run_id: int, source_path: str, build_path: str) -> int:
        stub = await self._get_stub()
        request = platform_service_pb2.CreateAppVersionRequest(
            app_id=app_id, agent_run_id=agent_run_id,
            source_path=source_path, build_path=build_path,
        )
        response = await stub.CreateAppVersion(request)
        return response.version_id

    async def get_chat_history(self, session_id: int, limit: int = 50) -> list[dict]:
        stub = await self._get_stub()
        request = platform_service_pb2.GetChatHistoryRequest(session_id=session_id, limit=limit)
        response = await stub.GetChatHistory(request)
        return [{"id": e.id, "role": e.role, "content": e.content} for e in response.entries]

    async def get_app_detail(self, app_id: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.GetAppDetailRequest(app_id=app_id)
        response = await stub.GetAppDetail(request)
        return {
            "id": response.id, "name": response.name,
            "description": response.description,
            "codeGenType": response.code_gen_type,
            "userId": response.user_id,
        }
```

**Step 5: 提交**

```bash
git add agent-runtime-python/app/grpc_client/ agent-runtime-python/app/core/config.py
git commit -m "feat: implement Python gRPC clients for ToolService and PlatformService"
```

---

### Task 5.2: 改造 Python Agent 使用 gRPC Client

**Files:**
- Modify: `agent-runtime-python/app/services/model_config_client.py` — 改用 `GrpcPlatformClient`
- Modify: `agent-runtime-python/app/agent/graph.py` — 改用 `GrpcToolClient` 替代本地 `FileTools`
- Modify: `agent-runtime-python/app/services/agent_service.py` — 注入 gRPC clients
- Modify: `agent-runtime-python/app/agent/state.py` — 添加 gRPC client 字段

**Step 1: 改造 AgentState**

在 state 中添加 `grpc_tool_client` 和 `grpc_platform_client` 字段：

```python
from typing import TypedDict
from langchain_core.language_models.chat_models import BaseChatModel
from app.events.agent_event import AgentEvent
from app.schemas.code_generation import CodeGenerationRequest
from app.grpc_client.tool_client import GrpcToolClient
from app.grpc_client.platform_client import GrpcPlatformClient


class AgentState(TypedDict):
    request: CodeGenerationRequest
    events: list[AgentEvent]
    model_config: dict | None
    chat_model: BaseChatModel | None
    generated_content: str | None
    error: str | None
    grpc_tool_client: GrpcToolClient | None
    grpc_platform_client: GrpcPlatformClient | None
```

**Step 2: 改造 graph.py 中的节点**

将 `write_file` 节点中的本地 `FileTools` 调用改为远程 gRPC 调用：

```python
async def write_file(state: AgentState) -> AgentState:
    request = state["request"]
    events = list(state["events"])
    seq = len(events) + 1
    generated_content = state.get("generated_content")
    tool_client = state.get("grpc_tool_client")

    if generated_content is None:
        events.append(AgentEvent(agentRunId=request.agentRunId, seq=seq, eventType="error", data={"message": "无生成内容，跳过文件写入"}))
        return {**state, "events": events, "generated_content": None, "error": state.get("error") or "无生成内容"}

    path = "src/App.vue"

    events.append(AgentEvent(agentRunId=request.agentRunId, seq=seq, eventType="tool_request", data={"id": "tool-1", "name": "write_file", "arguments": {"path": path}}))
    seq += 1

    if tool_client:
        result = await tool_client.write_file(path, generated_content)
    else:
        from app.tools.file_tools import FileTools
        from app.tools.workspace import Workspace
        workspace = Workspace(request.workspacePath or f"storage/agent-workspaces/{request.agentRunId}/source")
        tools = FileTools(workspace)
        result = tools.write_file(path, generated_content)

    events.append(AgentEvent(agentRunId=request.agentRunId, seq=seq, eventType="tool_executed", data={"id": "tool-1", "name": "write_file", "arguments": {"path": path}, "result": result}))
    seq += 1

    events.append(AgentEvent(agentRunId=request.agentRunId, seq=seq, eventType="done", data={"message": "completed"}))
    return {**state, "events": events, "generated_content": generated_content, "error": None}
```

**Step 3: 改造 AgentService**

用 `GrpcPlatformClient` 替代 `ModelConfigClient`：

```python
async def _resolve_chat_model(self, request: CodeGenerationRequest) -> tuple[dict | None, BaseChatModel | None]:
    if request.modelConfigId is None:
        return None, None
    try:
        config = await self._grpc_platform_client.get_model_config(request.modelConfigId, request.configVersion or 0)
        chat_model = self._chat_model_factory.create(config)
        return config, chat_model
    except Exception as e:
        logger.error("Failed to resolve chat model: %s", e)
        return None, None
```

**Step 4: 提交**

```bash
git add agent-runtime-python/app/agent/ agent-runtime-python/app/services/
git commit -m "feat: integrate gRPC clients into Python agent graph and services"
```

---

## Phase 6: 统一事件流 + 清理旧代码

### Task 6.1: 统一 CodeGenerationRuntime 接口

**Files:**
- Modify: `backend-java/src/main/java/com/adcage/acaicodefree/runtime/CodeGenerationRuntime.java` — 可选：返回类型改为更强类型
- Delete: `backend-java/src/main/java/com/adcage/acaicodefree/runtime/PythonAgentEvent.java`
- Delete: `backend-java/src/main/java/com/adcage/acaicodefree/runtime/PythonAgentEventMapper.java`

**Step 1: 删除不再需要的旧文件**

- `PythonAgentEvent.java` — gRPC 事件直接用 proto 生成类
- `PythonAgentEventMapper.java` — 映射逻辑已内置到 `GrpcPythonAgentRuntime`

**Step 2: 验证编译**

```bash
cd backend-java && mvn compile
```

**Step 3: 提交**

```bash
git add -A
git commit -m "refactor: remove deprecated HTTP+SSE Python agent runtime files"
```

---

### Task 6.2: Python 端清理旧 HTTP 回调代码

**Files:**
- Modify: `agent-runtime-python/app/services/model_config_client.py` — 标记 @deprecated 或删除
- Modify: `agent-runtime-python/app/api/code_generation.py` — FastAPI SSE 端点可保留作为备用
- Clean: `agent-runtime-python/app/events/config_subscriber.py` — 评估是否仍需 Redis 订阅

**Step 1: 标记 ModelConfigClient 为 deprecated**

在类文档字符串中标注已被 `GrpcPlatformClient` 替代。

**Step 2: 保留 FastAPI SSE 端点**

`/agent/code-generation/stream` 端点保留，作为 gRPC 不可用时的降级通道。但主要流量走 gRPC。

**Step 3: 提交**

```bash
git add agent-runtime-python/app/services/model_config_client.py
git commit -m "refactor: deprecate HTTP-based ModelConfigClient in favor of gRPC"
```

---

### Task 6.3: 端到端集成测试

**Files:**
- Create: `backend-java/src/test/java/com/adcage/acaicodefree/grpc/GrpcIntegrationTest.java`
- Modify: `backend-java/src/test/java/com/adcage/acaicodefree/controller/PythonAgentE2ETest.java`

**Step 1: 编写 Java gRPC Client 集成测试**

测试 `GrpcPythonAgentRuntime` 能否正确接收 Python 端的流式事件。

```java
@Slf4j
@SpringBootTest
class GrpcIntegrationTest {

    @Resource
    private CodeGenerationRuntimeRouter router;

    @Test
    void testPythonAgentRuntimeIsGrpc() {
        CodeGenerationRuntime runtime = router.select();
        // 需要配置 agent.runtime=python-agent
        assertThat(runtime).isInstanceOf(GrpcPythonAgentRuntime.class);
    }
}
```

**Step 2: 更新 E2E 测试**

修改现有的 `PythonAgentE2ETest`，确保 gRPC 通道工作正常。

**Step 3: 提交**

```bash
git add backend-java/src/test/
git commit -m "test: add gRPC integration tests"
```

---

## 风险与注意事项

| 风险 | 缓解措施 |
|------|----------|
| gRPC Server 端口与现有服务冲突 | 使用独立端口 9090/9091，与 HTTP 8700/9000 分离 |
| protobuf 代码生成路径问题 | proto 文件放在项目根目录，两端的构建脚本都指向同一 proto 源 |
| gRPC 内部认证安全 | 使用与现有 HTTP 相同的 `internal-secret` 机制，通过 gRPC metadata 传递 |
| Python agent 优雅关闭 | 在 FastAPI lifespan 中管理 gRPC server 的 start/stop |
| 旧 HTTP 通道兼容性 | Phase 6 中保留 FastAPI SSE 端点作为降级，不立即删除 |
| Java 端 ToolService 的 @ToolMemoryId 机制 | gRPC 请求中直接传 appId，ToolService 实现中手动解析路径 |
| ModelConfigRuntimeVO 的 apiKey 是否加密 | 当前 Python 端直接使用，保持一致；后续可在 PlatformService 中处理解密 |
| Spring Boot 与 gRPC Server 端口管理 | 使用 `grpc-spring-boot-starter`，gRPC Server 端口独立于 `server.port` |

---

## 文件变更总结

### 新增文件

| 文件 | 说明 |
|------|------|
| `proto/common.proto` | 共享消息类型和枚举 |
| `proto/code_generation.proto` | 代码生成服务定义 |
| `proto/tool_service.proto` | 文件工具服务定义 |
| `proto/platform_service.proto` | 平台服务定义 |
| `backend-java/.../grpc/server/GrpcToolService.java` | Java gRPC ToolService 实现 |
| `backend-java/.../grpc/server/GrpcPlatformService.java` | Java gRPC PlatformService 实现 |
| `backend-java/.../grpc/server/GrpcInternalAuthInterceptor.java` | gRPC 认证拦截器 |
| `backend-java/.../grpc/client/GrpcPythonAgentRuntime.java` | Java gRPC Client（替代 PythonAgentRuntime） |
| `agent-runtime-python/scripts/generate_grpc.py` | Python gRPC 代码生成脚本 |
| `agent-runtime-python/app/grpc/` | Python 生成的 gRPC 代码（*_pb2.py, *_pb2_grpc.py） |
| `agent-runtime-python/app/grpc_server/server.py` | Python gRPC Server 启动 |
| `agent-runtime-python/app/grpc_server/code_generation_servicer.py` | Python CodeGenerationService 实现 |
| `agent-runtime-python/app/grpc_client/channel.py` | Python gRPC Channel 管理 |
| `agent-runtime-python/app/grpc_client/tool_client.py` | Python ToolService Client |
| `agent-runtime-python/app/grpc_client/platform_client.py` | Python PlatformService Client |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend-java/pom.xml` | 添加 gRPC 依赖和 protobuf-maven-plugin |
| `backend-java/.../resources/application.yml` | 添加 gRPC server/client 配置 |
| `backend-java/.../runtime/impl/PythonAgentRuntime.java` | 标记 @Deprecated，注释 @Component |
| `backend-java/.../service/impl/AppServiceImpl.java` | 删除 python-agent 分支，统一流处理 |
| `agent-runtime-python/pyproject.toml` | 添加 grpcio 依赖 |
| `agent-runtime-python/app/core/config.py` | 添加 gRPC 配置项 |
| `agent-runtime-python/app/main.py` | 添加 gRPC server lifespan 管理 |
| `agent-runtime-python/app/agent/state.py` | 添加 gRPC client 字段 |
| `agent-runtime-python/app/agent/graph.py` | 改用 gRPC ToolClient |
| `agent-runtime-python/app/services/agent_service.py` | 注入 gRPC clients |
| `agent-runtime-python/app/services/model_config_client.py` | 标记 deprecated |

### 删除文件

| 文件 | 说明 |
|------|------|
| `backend-java/.../runtime/PythonAgentEvent.java` | 被 proto 生成类替代 |
| `backend-java/.../runtime/PythonAgentEventMapper.java` | 映射逻辑内置到 GrpcPythonAgentRuntime |
