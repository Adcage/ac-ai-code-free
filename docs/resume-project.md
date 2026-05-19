**AC AI Code Free — AI 智能编程辅助平台** https://github.com/Adcage/ac-ai-code-free

技术栈：Spring Boot 3、LangChain4j、MyBatis-Flex、Caffeine、Redis、Selenium、COS、Vue3、TypeScript、Vite、Ant Design Vue、Pinia

设计 AI 代码生成引擎，以 Facade + 策略 + 模板方法三层架构编排生成流程；通过 LangChain4j 声明式接口定义 6 个 AI 服务方法，配合 Caffeine 缓存（appId+类型隔离）动态构建实例，按代码生成类型切换流处理器与文件保存策略。

设计 AI 工具调用系统（readFile/writeFile/modifyFile/deleteFile/readDir），通过 ToolManager 统一注册管理；实现路径穿越防护（normalize 校验）与关键文件删除保护机制，保障 AI 自主生成 Vue 工程时的文件系统安全。

基于 Reactor Flux + SSE 实现流式代码生成，TokenStream 逐 token 推送（首字 < 1s）；设计流式聚合保存机制，流结束后解析完整代码块再写入文件，Vue 工程模式自动触发 npm install + build 并支持依赖版本自动修复。

设计 iframe 注入式可视化编辑器，通过 postMessage 双向通信与 IIFE 脚本注入实现元素选中；构建 CSS 选择器自动生成算法（8 层深度），选中元素信息自动拼接 prompt，配合创建/修改分流机制路由至差异化 AI 接口实现增量修改。

实现 AI 智能路由（显式指定 > AI 路由 > 默认兜底三级策略）；Selenium 无头截图 + COS 上传异步生成封面图；一键部署与源码下载全链路闭环。
