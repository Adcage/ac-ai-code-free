# Task 7 Build Preview And Deploy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `vue_project` 模式补齐固定构建流程，让生成结果从“源码目录”升级为“可构建、可预览、可部署的静态产物”。

**Architecture:** 这一步把 AI 能力和平台能力彻底分开。AI 只负责写项目文件，构建、预览、部署全部由后端程序固定执行；构建的可信结果是 `dist` 目录，而不是 `src` 或项目根目录。这样后面无论前端生成质量如何，平台侧都能用统一规则验收和部署。

**Tech Stack:** Java ProcessBuilder, Node.js, npm, Vite, Spring Service, Static Resource Mapping

---

## Files

- Create: `src/main/java/com/adcage/acaicodefree/core/build/VueProjectBuildService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java`
- Modify: `src/main/java/com/adcage/acaicodefree/config/WebMvcConfig.java`
- Test: `src/test/java/com/adcage/acaicodefree/core/build/VueProjectBuildServiceTest.java`

## 当前问题

当前系统的问题不是“不会部署”，而是部署对象错了：

- 现在直接复制 `codeGenType_appId` 目录。
- 对于 Vue 工程，这个目录是源码目录，不是可上线静态目录。
- 前端预览地址也仍指向 `${codeGenType}_${appId}/index.html`，这与 Vite 工程的产物结构不匹配。

## 详细步骤

### Step 1: 先写构建服务测试

测试目标至少覆盖：

```java
@Test
void shouldRunNpmInstallAndBuildInVueProjectDirectory() {}

@Test
void shouldUseNpmCmdOnWindows() {}

@Test
void shouldFailWhenDistDirectoryMissingAfterBuild() {}
```

如果构建命令执行不适合做纯单测，可把“命令构造”和“路径计算”拆为可单测方法。

### Step 2: 新建 `VueProjectBuildService`

职责必须集中：

- 根据 `appId` 定位 `temp/code_output/vue_project_{appId}`。
- 执行 `npm install`。
- 执行 `npm run build`。
- 收集 stdout / stderr。
- 处理超时。
- 检查 `dist` 是否存在。

实现约束：

- Windows 使用 `npm.cmd`。
- Unix 使用 `npm`。
- `npm install` 和 `npm run build` 分开执行。
- 任一步退出码非 0 都应视为失败。

### Step 3: 修改 `AppServiceImpl#chatToGenCode`

在 `vue_project` 流成功完成后，增加固定构建动作：

- AI 文件生成成功
- 后端执行 `npm install`
- 后端执行 `npm run build`
- 如果失败，把错误摘要补入本次 AI 结果或错误日志

这一步要注意用户体验：

- 不能把构建动作交给 AI。
- 不能要求用户手动构建。
- 构建失败时要有可读错误信息，不能只有栈追踪。

### Step 4: 修改 `deployApp()`

目标逻辑：

- 非 `vue_project` 继续复制源码目录。
- `vue_project` 优先检查 `dist` 目录。
- `dist` 不存在时自动触发构建。
- 构建成功后复制 `dist` 到 `temp/code_deploy/{deployKey}`。

这一步是整个“能部署”的真正关键。

### Step 5: 检查 `WebMvcConfig`

通常不需要大改映射规则，因为当前已经把 `temp/code_output` 和 `temp/code_deploy` 映射到了 `/static/**`。

但要检查并确认：

- `vue_project_{appId}/dist/index.html` 能被静态资源映射命中。
- 文档里写的预览路径与真实访问路径一致。

### Step 6: 运行构建服务测试

执行：

```bash
mvn -Dtest=VueProjectBuildServiceTest test
```

然后做一次真实手工验证：

1. 准备一个最小 Vite Vue 项目目录。
2. 放进 `temp/code_output/vue_project_{appId}`。
3. 调用构建服务。
4. 确认 `dist` 生成成功。

### Step 7: 验证预览和部署路径

验证两条路径：

- 预览：`/api/static/vue_project_{appId}/dist/index.html`
- 部署：`http://localhost/{deployKey}/`

手工确认：

- 页面可打开。
- 静态资源可加载。
- 使用子路径访问时不丢失资源。

### Step 8: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/core/build/VueProjectBuildService.java src/main/java/com/adcage/acaicodefree/service/impl/AppServiceImpl.java src/main/java/com/adcage/acaicodefree/config/WebMvcConfig.java src/test/java/com/adcage/acaicodefree/core/build/VueProjectBuildServiceTest.java
git commit -m "feat: build and deploy generated vue projects"
```

## 验收标准

- 生成完成后后端会固定执行构建。
- `vue_project` 预览路径指向 `dist/index.html`。
- `vue_project` 部署复制的是 `dist` 目录。
- 构建失败时可以看到可读日志摘要。

## 风险说明

- 如果把构建动作塞到 AI 工具里，平台控制权会丢失。
- 如果继续部署源码目录，用户看到的“已部署”其实是无效结果。
