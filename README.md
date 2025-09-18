# ac-ai-code-free

> 基于 Spring Boot 和 Vue 的 AI 编程辅助平台，提供低代码开发体验与智能编码支持

## 项目简介

**ac-ai-code-free** 是一个面向开发者的 AI 编程辅助平台，采用前后端分离架构，旨在通过自动化代码生成、智能接口管理、权限控制等功能提升开发效率。项目核心价值：

- ✨ **低代码开发**：通过 MyBatis-Flex Codegen 自动生成实体类与 Mapper
- 📚 **可视化 API 文档**：集成 Knife4j 提供交互式接口文档
- 🔒 **精细化权限控制**：基于注解的接口级权限管理（`@AuthCheck`）
- 🌐 **前后端分离**：Vue 3 前端 + Spring Boot 3.5.5 后端架构

## 技术栈

### 后端
- **核心框架**: Spring Boot 3.5.5 (Jakarta EE)
- **ORM**: MyBatis-Flex 1.11.0（支持代码生成）
- **API 文档**: Knife4j OpenAPI3 4.4.0
- **工具库**: Lombok 1.18.38 + Hutool 5.8.38
- **数据库**: MySQL 5.7+
- **开发语言**: Java 21
- **构建工具**: Maven

### 前端
- **核心框架**: Vue 3 + TypeScript
- **构建工具**: Vite 5.0+
- **HTTP 客户端**: Axios
- **状态管理**: Pinia（简易 store 实现）
- **代码规范**: ESLint + Prettier

## 功能特性

| 模块 | 功能点 |
|------|--------|
| **用户系统** | 注册/登录、权限分级（ADMIN/USER）、个人信息管理 |
| **API 管理** | 健康检查接口、统一响应格式（`BaseResponse<T>`） |
| **开发辅助** | MyBatis-Flex 代码生成、OpenAPI 类型自动生成 |
| **安全控制** | JWT 认证、CORS 配置、AOP 权限拦截 |
| **运维支持** | 请求日志记录、全局异常处理 |

## 快速开始

### 环境准备
1. JDK 21
2. Maven 3.6+
3. Node.js 18+
4. MySQL 5.7+

### 安装步骤

#### 1. 初始化数据库
```
-- 将 sql/create_table.sql 导入到您的 MySQL 数据库中
-- 可通过 MySQL Workbench、命令行或其他数据库管理工具执行
```

#### 2. 配置数据库连接
修改 `src/main/resources/application.yml` 中的数据库配置：
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ac_ai_code_free?useSSL=false
    username: root
    password: your_password
```

#### 3. 启动后端服务
```bash
# 在项目根目录执行
mvn spring-boot:run
```

#### 4. 启动前端服务
```bash
cd ac-ai-code-free-fronted
npm install
npm run dev
```

### 访问地址
- 前端开发服务器: http://localhost:5173
- 后端 API 文档: http://localhost:8080/doc.html

## 项目结构

```
ac-ai-code-free
├── ac-ai-code-free-fronted  # Vue 前端项目
│   ├── src
│   │   ├── api            # API 接口定义
│   │   ├── components     # 公共组件
│   │   ├── pages          # 页面组件
│   │   └── ...            # 其他前端资源
├── src                    # Spring Boot 后端
│   ├── main
│   │   ├── java           # Java 源码
│   │   └── resources      # 资源文件
├── sql                    # 数据库脚本
│   └── create_table.sql
└── pom.xml                # Maven 配置
```

## 代码规范

- **命名规范**: 遵循 camelCase 变量命名（TypeScript/Java）
- **注解规范**: 
  - 权限控制使用 `@AuthCheck` 注解
- **异常处理**: 统一返回 `BaseResponse` 格式
- **日志规范**: 通过 AOP 记录请求日志（`LogInterceptor`）

## 许可证

[MIT](LICENSE)