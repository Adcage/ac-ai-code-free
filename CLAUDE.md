# AGENTS.md - AI 编程助手指南

## 项目概述

ac-ai-code-free 是基于 Spring Boot 3.5.5 + Vue 3 的 AI 编程辅助平台，前后端分离架构。后端使用 MyBatis-Flex ORM、LangChain4j AI 集成、Caffeine 缓存；前端使用 Ant Design Vue、Pinia、Axios。

## 构建/测试/开发命令

### 后端（backend-java/ 目录执行）

```bash
mvn spring-boot:run                    # 启动开发服务器
mvn clean package                      # 构建项目
mvn test                               # 运行所有测试
mvn test -Dtest=UserServiceTest        # 运行单个测试类
mvn test -Dtest=UserServiceTest#testUserRegister  # 运行单个测试方法
mvn clean package -DskipTests          # 跳过测试构建
```

### 前端（frontend-vue/ 目录执行）

```bash
npm install                            # 安装依赖
npm run dev                            # 启动开发服务器 (http://localhost:5173)
npm run build                          # 类型检查 + 构建
npm run build-only                     # 仅构建（不进行类型检查）
npm run type-check                     # TypeScript 类型检查 (vue-tsc)
npm run lint                           # ESLint 检查并自动修复
npm run format                         # Prettier 格式化 src/ 目录
npm run openapi                        # 从后端 OpenAPI 生成 TypeScript 类型和 API 函数
```

## 后端代码风格（Java 17 + Spring Boot）

### 目录结构

```
backend-java/src/main/java/com/adcage/acaicodefree/
├── ai/              # LangChain4j AI 集成（声明式服务接口、工厂、工具）
├── annotation/      # 自定义注解 (@AuthCheck)
├── aop/             # AOP 切面 (AuthInterceptor, LogInterceptor)
├── common/          # 通用类 (BaseResponse, ErrorCode, ResultUtils, PageRequest, DeleteRequest)
├── config/          # 配置类 (CorsConfig, JsonConfig, WebMvcConfig)
├── constant/        # 常量接口 (UserConstant, AppConstant)
├── controller/       # 控制器层
├── core/            # 核心业务编排（Facade + 策略 + 模板方法模式）
│   ├── build/        # 项目构建服务 (VueProjectBuildService)
│   ├── handler/      # 流处理器策略 (SimpleTextStreamHandler, JsonMessageStreamHandler)
│   ├── memory/       # AI 聊天记忆加载 (ChatMemoryLoader)
│   ├── parser/       # 代码解析策略 (SingleFileParser, MultiFileParser)
│   └── saver/        # 文件保存模板方法 (AbstractCodeFileSaver 及子类)
├── exception/       # 异常 (BusinessException, GlobalExceptionHandler, ThrowUtils)
├── generator/       # MyBatis-Flex 代码生成器 (独立 main 方法)
├── mapper/          # MyBatis-Flex Mapper 接口（继承 BaseMapper）
├── model/
│   ├── dto/          # 请求 DTO（按领域分子包: app/, chat/, user/）
│   ├── entity/       # 数据库实体 (@Table, @Id, @Column)
│   ├── enums/        # 枚举 (CodeGenTypeEnum, UserRoleEnum)
│   └── vo/          # 响应 VO（按领域分子包）
└── service/          # 服务层接口 + impl/ 实现
```

### 命名与编码规范

- **类名** PascalCase：`UserController`, `BusinessException`
- **方法/变量** camelCase：`userRegister`, `loginUser`
- **常量** UPPER_SNAKE_CASE：`ADMIN_ROLE`, `DEFAULT_PASSWORD`
- **常量类** 使用 `interface` 而非 `class`：`public interface UserConstant { String ADMIN_ROLE = "admin"; }`
- **包名** 全小写：`com.adcage.acaicodefree`

### API 响应格式

所有接口返回 `BaseResponse<T>`（code=0 表示成功）：

```java
return ResultUtils.success(data);                                       // 成功
throw new BusinessException(ErrorCode.PARAMS_ERROR);                    // 错误（无消息）
throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "自定义消息");    // 错误（带消息）
ThrowUtils.throwIf(id <= 0, ErrorCode.PARAMS_ERROR);                    // 条件抛异常
```

### 错误码

| code | 含义 | | code | 含义 |
|------|------|-|------|------|
| 0 | 成功 | | 40101 | 无权限 |
| 40000 | 请求参数错误 | | 40300 | 禁止访问 |
| 40100 | 未登录 | | 40400 | 请求数据不存在 |
| 50000 | 系统内部异常 | | 50001 | 操作失败 |

### Controller 模式

```java
@RestController @RequestMapping("/app")
public class AppController {
    @Resource private AppService appService;
    @Resource private UserService userService;

    @PostMapping("/add")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)    // 管理员权限
    public BaseResponse<Long> addApp(@RequestBody AppAddRequest request) { ... }

    @PostMapping("/list/page/vo")                      // 分页查询返回 VO
    public BaseResponse<Page<AppVO>> listAppVOByPage(@RequestBody AppQueryRequest request) { ... }

    @PostMapping("/delete")                             // 删除使用共享 DeleteRequest
    public BaseResponse<Boolean> deleteApp(@RequestBody DeleteRequest request) { ... }
}
```

### Service 模式

- 接口继承 `IService<Entity>`，实现类继承 `ServiceImpl<Mapper, Entity>`
- 构造器注入依赖（非 `@Autowired` 字段注入）
- Entity→VO 转换在 Service 层完成：`BeanUtil.copyProperties(entity, vo)` + 关联数据填充
- 校验方法：`void validXxx(Entity entity, boolean add)` 区分新增/更新

### Entity 模式

```java
@Data @Builder @NoArgsConstructor @AllArgsConstructor
@Table("user")
public class User implements Serializable {
    @Id(keyType = KeyType.Generator, value = KeyGenerators.snowFlakeId)
    private Long id;
    @Column(value = "isDelete", isLogicDelete = true)
    private Integer isDelete;
    @Column(value = "updateTime", onUpdateValue = "now()")
    private LocalDateTime updateTime;
}
```

### DTO/VO 约定

| 类型 | 用途 | 有 ID | 继承 |
|------|------|-------|------|
| `*AddRequest` | 创建操作 | 否 | 否 |
| `*EditRequest` | 自助编辑（ID 从 session 取） | 否 | 否 |
| `*UpdateRequest` | 管理员更新 | 是 | 否 |
| `*QueryRequest` | 分页查询 | 可选 | `PageRequest` |
| `DeleteRequest` | 通用删除 | 是 | 否 |
| `*VO` | API 响应 | 是 | 否 |

### SSE 流式端点

AI 对话生成使用 `Flux<ServerSentEvent<String>>` 返回流式数据，路径 `/app/chat/gen/code/stream`。

## 前端代码风格（Vue 3 + TypeScript）

### 目录结构

```
frontend-vue/src/
├── access/        # 路由守卫（登录/权限检查）
├── api/           # 自动生成的 API 调用函数及类型（由 openapi2ts 生成，勿手动编辑）
├── assets/        # 静态资源
├── components/    # 可复用组件
├── layouts/       # 布局组件 (BasicLayout)
├── pages/         # 页面（按领域分目录: admin/, app/, user/）
├── router/        # 路由（自动发现 .ts 文件，每个文件导出 RouteRecordRaw 数组）
├── stores/        # Pinia 状态管理
├── request.ts     # Axios 实例及拦截器
├── App.vue         # 根组件
└── main.ts         # 入口文件
```

### 格式化配置

- **Prettier**：`semi: false`, `singleQuote: true`, `printWidth: 120`
- **EditorConfig**：缩进 2 空格，行尾 LF，最大行长 100
- **ESLint**：flat config，`eslint-plugin-vue` essential + `@vue/eslint-config-typescript`

### Vue 组件规范

```vue
<template><!-- 模板 --></template>
<script lang="ts" setup>
  // 导入 → 响应式数据 → 计算属性 → 函数 → 生命周期钩子
</script>
<style scoped>/* 作用域样式 */</style>
```

- Props 使用 TypeScript 接口 + `withDefaults(defineProps<Props>(), { ... })`
- 暴露方法给父组件：`defineExpose({ open })`
- 所有文本使用中文（无 i18n）

### 状态管理（Pinia）

使用 Composition API 风格 `defineStore`，所有 Store 放在 `src/stores/` 下。

### API 调用模式

- API 函数由 `@umijs/openapi` 自动生成，存放于 `src/api/`，**勿手动编辑**
- 调用返回 Axios 响应，成功判断 `res.data.code === 0`，数据取 `res.data.data`
- 拦截器自动处理 40100（未登录跳转）和网络错误提示
- 认证方式：Cookie-based（`withCredentials: true`）

### 环境变量

| 文件 | 关键变量 |
|------|----------|
| `.env.development` | `VITE_API_BASE_URL=http://localhost:8700/api` |
| `.env.production` | `VITE_API_BASE_URL=https://your-api-domain.com/api` |

## 重要注意事项

1. **Java 版本**：JDK 17 | **Node.js 版本**：`^20.19.0 || >=22.12.0`
2. **数据库**：MySQL 5.7+，建表脚本 `sql/create_table.sql`
3. **后端 API 文档**：`http://localhost:8080/doc.html`（Knife4j）
4. **前端开发服务器**：`http://localhost:5173` | **后端 API 基础路径**：`http://localhost:8700/api`
5. **路径分隔符**：所有文件路径统一使用正斜杠 `/`，禁止反斜杠 `\`
6. **MyBatis-Flex 代码生成**：运行 `generator.MyBatisCodegen` 的 main 方法可从数据库表生成 Entity/Mapper/Service/Controller
7. **API 类型同步**：修改后端接口后，在前端目录执行 `npm run openapi` 重新生成 TypeScript 类型
8. **AI 服务**：使用 LangChain4j 声明式接口（`@SystemMessage`, `@UserMessage`），通过 `AiCodeGenServiceFactory` 获取缓存的服务实例
