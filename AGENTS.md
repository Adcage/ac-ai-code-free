# AGENTS.md - AI 编程助手指南

> 本文件为 AI 编程助手（如 Claude、Copilot）提供代码库规范和开发指南

## 项目概述

ac-ai-code-free 是一个基于 Spring Boot 3.5.5 + Vue 3 的 AI 编程辅助平台，采用前后端分离架构。

## 构建/测试/开发命令

### 后端 (根目录)

```bash
# 启动开发服务器
mvn spring-boot:run

# 构建项目
mvn clean package

# 运行所有测试
mvn test

# 运行单个测试类
mvn test -Dtest=UserServiceTest

# 运行单个测试方法
mvn test -Dtest=UserServiceTest#testUserRegister

# 跳过测试构建
mvn clean package -DskipTests
```

### 前端 (ac-ai-code-free-fronted/)

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run type-check

# 代码检查并自动修复
npm run lint

# 格式化代码
npm run format

# 从后端 OpenAPI 生成 TypeScript 类型
npm run openapi2ts
```

## 代码风格指南

### 后端 (Java)

#### 命名规范
- **类名**: PascalCase (如 `UserController`, `BusinessException`)
- **方法/变量**: camelCase (如 `userRegister`, `loginUser`)
- **常量**: UPPER_SNAKE_CASE (如 `ADMIN_ROLE`, `DEFAULT_PASSWORD`)
- **包名**: 全小写 (如 `com.adcage.acaicodefree`)

#### 目录结构
```
src/main/java/com/adcage/acaicodefree/
├── annotation/     # 自定义注解 (@AuthCheck)
├── aop/            # AOP 切面 (LogInterceptor, AuthInterceptor)
├── common/         # 通用类 (BaseResponse, ErrorCode, ResultUtils)
├── config/         # 配置类 (CorsConfig, JsonConfig)
├── controller/     # 控制器层
├── exception/      # 异常处理 (BusinessException, GlobalExceptionHandler)
├── mapper/         # MyBatis-Flex Mapper
├── model/
│   ├── dto/        # 数据传输对象 (Request)
│   ├── entity/     # 数据库实体
│   ├── enums/      # 枚举类
│   └── vo/         # 视图对象 (Response)
└── service/        # 服务层
    └── impl/       # 服务实现
```

#### 响应格式
所有 API 返回统一的 `BaseResponse<T>` 格式：
```java
// 成功响应
return ResultUtils.success(data);

// 错误响应
throw new BusinessException(ErrorCode.PARAMS_ERROR);
throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "自定义错误信息");
```

#### 权限控制
使用 `@AuthCheck` 注解进行接口级权限控制：
```java
@AuthCheck(mustRole = UserConstant.ADMIN_ROLE)  // 仅管理员
public BaseResponse<User> getUserById(long id) { ... }
```

#### 参数校验
使用 `ThrowUtils` 进行参数校验：
```java
ThrowUtils.throwIf(userRequest == null, ErrorCode.PARAMS_ERROR);
ThrowUtils.throwIf(id <= 0, ErrorCode.PARAMS_ERROR);
```

#### 错误码定义
| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 40000 | 请求参数错误 |
| 40100 | 未登录 |
| 40101 | 无权限 |
| 40400 | 请求数据不存在 |
| 50000 | 系统内部异常 |
| 50001 | 操作失败 |

### 前端 (Vue 3 + TypeScript)

#### Prettier 配置
- 无分号 (`semi: false`)
- 单引号 (`singleQuote: true`)
- 行宽 120 字符 (`printWidth: 120`)

#### ESLint 配置
- 使用 `@vue/eslint-config-typescript` 和 `eslint-plugin-vue`
- Vue 使用 `flat/essential` 规则集

#### 导入规范
```typescript
// Vue 核心
import { ref, computed, onMounted, reactive } from 'vue'
import { defineStore } from 'pinia'

// 路由
import router from '@/router'
import type { RouteRecordRaw } from 'vue-router'

// API 调用
import { getLoginUser, userLogout } from '@/api/userController.ts'

// UI 组件
import { message } from 'ant-design-vue'
import { DownOutlined, EyeOutlined } from '@ant-design/icons-vue'

// 工具库
import dayjs from 'dayjs'
```

#### 路径别名
- 使用 `@/` 作为 `src/` 目录的别名

#### Vue 组件结构
```vue
<template>
  <!-- 模板内容 -->
</template>
<script lang="ts" setup>
// 导入
// 响应式数据
// 计算属性
// 函数定义
// 生命周期钩子
</script>
<style scoped>
/* 组件样式 */
</style>
```

#### 状态管理 (Pinia)
使用 Composition API 风格定义 Store：
```typescript
export const useLoginUserStore = defineStore('loginUser', () => {
  const loginUser = ref<API.LoginUserVO>({})
  async function fetchLoginUser() { ... }
  return { loginUser, fetchLoginUser }
})
```

#### API 调用模式
- API 函数由 `@umijs/openapi` 从后端 OpenAPI 规范自动生成
- 所有 API 响应通过 Axios 拦截器统一处理
- 未登录时自动跳转到登录页（错误码 40100）

## 重要注意事项

1. **Node.js 版本**: 需要 `^20.19.0 || >=22.12.0`
2. **Java 版本**: 需要 JDK 21
3. **数据库**: MySQL 5.7+
4. **后端 API 文档**: 启动后访问 `http://localhost:8080/doc.html`
5. **前端开发服务器**: `http://localhost:5173`
6. **后端 API 基础路径**: `http://localhost:8700/api`

## 文件路径规则

所有文件路径统一使用正斜杠（/）作为分隔符，禁止使用反斜杠（\）。
