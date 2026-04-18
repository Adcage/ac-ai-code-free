# Task 2 Entry Points Enum Dto Prompt Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为第七阶段打开正式的 `vue_project` 业务入口，让应用创建、模式识别和系统提示词资源都具备真实接入点。

**Architecture:** 这一任务只处理“入口打开”问题，不提前做底层实现。通过扩展枚举、请求 DTO、控制层入参和 Prompt 资源，把 `vue_project` 从文档概念变成后端可识别、前端可传递、模型可引用的正式模式。

**Tech Stack:** Java, Spring MVC, DTO, Enum, LangChain4j Prompt Resource

---

## Files

- Modify: `src/main/java/com/adcage/acaicodefree/model/enums/CodeGenTypeEnum.java`
- Modify: `src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java`
- Modify: `src/main/java/com/adcage/acaicodefree/controller/AppController.java`
- Create: `src/main/resources/prompt/codegen-vue-project-system-prompt.txt`
- Test: `src/test/java/com/adcage/acaicodefree/controller/AppControllerTest.java`

## 当前问题

当前入口层的问题是显式的：

- 枚举里没有 `vue_project`。
- 创建应用请求 DTO 没有 `codeGenType` 字段。
- 控制层还在强制写死 `multi-file`。
- 系统 Prompt 资源文件还不存在，后续就算模型方法加好了也没法通过资源路径注入。

## 详细步骤

### Step 1: 先写控制层入参校验测试

如果项目当前已有控制层测试基线，先新增一个最小测试，验证两个场景：

```java
@Test
void addAppShouldAcceptVueProjectCodeGenType() {
    // 构造 AppAddRequest，包含 initPrompt 和 codeGenType=vue_project
    // 断言接口返回成功
}

@Test
void addAppShouldRejectUnknownCodeGenType() {
    // 构造非法 codeGenType
    // 断言返回参数错误
}
```

如果暂时没有控制层测试基线，至少在任务记录里写明这两个场景必须通过手工接口验证覆盖。

### Step 2: 修改 `CodeGenTypeEnum`

新增枚举值：

```java
VUE_PROJECT("Vue 工程模式", "vue_project")
```

同时确认下面两个点：

- `getEnumByValue()` 不需要特殊逻辑，新增值后应该自然可识别。
- 不要改旧值 `single_file` 和 `multi-file`，避免历史数据失效。

### Step 3: 修改 `AppAddRequest`

新增字段：

```java
private String codeGenType;
```

本任务不强制在 DTO 上堆很多注解，校验逻辑可以先保留在控制层，原因是当前项目整体风格就是在控制层用 `ThrowUtils` 做显式校验。

### Step 4: 修改 `AppController#addApp`

把当前这段硬编码去掉：

```java
app.setCodeGenType(CodeGenTypeEnum.MULTI_FILE.getValue());
```

替换为：

- 从 `appAddRequest` 读取 `codeGenType`
- 使用 `CodeGenTypeEnum.getEnumByValue()` 校验
- 非法值直接抛参数错误
- 合法值写入 `app.setCodeGenType(...)`

注意：

- 本任务不再让后端控制层决定默认值。
- 默认值交给前端创建应用时明确传入，避免控制层和前端状态不一致。

### Step 5: 新建 Prompt 资源

创建文件：`src/main/resources/prompt/codegen-vue-project-system-prompt.txt`

内容必须覆盖下面约束：

- 强制用 `writeFile` 工具逐文件写入。
- 强制 `vite.config.js` 使用 `base: './'`。
- 强制路由使用 `createWebHashHistory()`。
- 默认使用 Vue 3 + Vite + Vue Router 4 + JavaScript + 原生 CSS。
- 页面内容必须使用中文。
- 不生成 `node_modules`、`dist`、README 等冗余内容。

这个 Prompt 文件的目标不是追求文案优美，而是最大化减少生成不稳定性。

### Step 6: 运行接口验证

如果走测试：

```bash
mvn -Dtest=AppControllerTest test
```

如果走手工验证：

1. 调用 `/app/add`。
2. 传入 `initPrompt` 和 `codeGenType=vue_project`。
3. 确认数据库记录中 `codeGenType` 已保存为 `vue_project`。

还要补一个非法值验证：

1. 传入 `codeGenType=abc`。
2. 确认接口返回参数错误，而不是静默落成默认值。

### Step 7: 提交

```bash
git add src/main/java/com/adcage/acaicodefree/model/enums/CodeGenTypeEnum.java src/main/java/com/adcage/acaicodefree/model/dto/app/AppAddRequest.java src/main/java/com/adcage/acaicodefree/controller/AppController.java src/main/resources/prompt/codegen-vue-project-system-prompt.txt src/test/java/com/adcage/acaicodefree/controller/AppControllerTest.java
git commit -m "feat: add vue project generation entrypoint"
```

## 验收标准

- `CodeGenTypeEnum` 已包含 `vue_project`。
- 创建应用时不再硬编码 `multi-file`。
- 后端可以接收并保存 `codeGenType=vue_project`。
- Prompt 资源文件已经存在，后续 AI Service 可以直接引用。

## 风险说明

- 如果控制层直接给了默认值，会让前端状态和后端实际模式不一致。
- 如果 Prompt 资源写得过于松散，后续模型会更容易产生多余文件、错误路由模式和错误依赖。

## 完成记录

- 日期：2026-04-14
- 状态：已完成
- 结果：已新增 `CodeGenTypeEnum.VUE_PROJECT` 与 `AppAddRequest.codeGenType`，`AppController#addApp` 已切换为按请求参数校验并保存，不再硬编码 `multi-file`；已新增 `prompt/codegen-vue-project-system-prompt.txt`。
- 验证：`mvn clean "-Dtest=AppControllerTest#addAppShouldAcceptVueProjectCodeGenType,AppControllerTest#addAppShouldRejectUnknownCodeGenType" test` 通过。
