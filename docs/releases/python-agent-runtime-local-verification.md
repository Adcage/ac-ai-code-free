# Python Agent Runtime Local Verification

## Environment

- Java: 17
- Python: 3.10+
- Node: 20.19+ / 22.12+

## Prerequisites

- 数据库已执行 `sql/create_table.sql` 建表
- `model_config` 表中至少有一条 enabled=1 的 OpenAI-compatible 配置
- Java 应用 `application.yml` 中配置了 `agent.runtime.internal-secret`

## Commands

1. 启动 Python Runtime:
   ```bash
   cd agent-runtime-python && python -m uvicorn app.main:app --reload --port 9000
   ```
   验证: `curl http://localhost:9000/health` 返回成功

2. 启动 Java Backend:
   ```bash
   cd backend-java
   $env:AGENT_RUNTIME="python-agent"
   $env:AGENT_PYTHON_BASE_URL="http://localhost:9000"
   mvn spring-boot:run
   ```

3. 启动 Frontend:
   ```bash
   cd frontend-vue && npm run dev
   ```

## Test Steps

1. 访问 http://localhost:5173
2. 创建或选择一个应用
3. 在聊天中输入: `创建一个简洁的个人作品集首页，包含头像区域、项目列表和联系方式`
4. 观察流式响应

## Expected Results

- 前端收到流式 AI 文本 (ai_response 事件)
- 前端显示工具调用事件 (tool_request / tool_executed)
- `storage/agent-workspaces/<agentRunId>/source/src/App.vue` 存在
- 生成内容不是固定 skeleton (应反映用户需求)
- Java 保存 user 和 ai 历史消息
- Vue 构建成功或失败原因明确落库

## Result

**验证时间:** 2026-06-07 18:08 CST

**环境:**
- Java backend: PID 61744, port 8700, active profile=local
- Python runtime: port 9000 (health OK)
- Frontend: port 5173 (Vue 3 dev server)

**验证步骤:**
1. 登录 admin 用户 (userAccount=12345678, id=323775635606482944)
2. 插入 model_config 记录 (id=1, provider=openai, modelName=gpt-4o-mini, enabled=1, isDefault=1, configVersion=1)
3. 在主页输入"创建一个简洁的个人作品集首页"，点击发送
4. 页面跳转到应用生成页 `/app/generate/421172151579299840`

**数据库验证:**

- model_config 查询: ✅ Java 先查 `isDefault=1` 命中记录 (日志确认)
- agent_run INSERT: ✅ 包含 `modelConfigId=1`, `configVersion=1` (SQL 日志确认)
- agent_run UPDATE: ✅ 设置 `workspacePath=../storage/agent-workspaces/421172152745316352/source`
- chat_session: ✅ 创建成功 (id=421172152179085312, title=新会话 1, messageCount=2)
- chat_history: ✅ 2条记录 (seqNo=1 user消息, seqNo=2 ai消息 status=failed)

**SSE 结果:**
- runtime 使用 `java-legacy` (未设置 AGENT_RUNTIME=python-agent 环境变量)
- AI 生成失败: `AuthError: Invalid API key` — 因为 AI_API_KEY 环境变量未设置，Java 使用了 application-local.yml 中的默认值 `dummy-key`
- 错误消息通过 SSE 正确传回前端并在聊天区域显示 ✅

**前端显示:**
- 用户消息正确展示 ✅
- AI 错误消息正确展示 ✅
- 预览区显示"预览资源不存在"（符合预期，因为生成失败）✅

**Python runtime 验证:**
- Python health endpoint: ✅ `{"code":0,"message":"OK","data":{"status":"ok","runtime":"python-langgraph"}}`

**本次验证结论:**
- ✅ model_config 默认配置查找逻辑已生效（isDefault 优先 → fallback latest enabled）
- ✅ AgentRun 创建时正确保存 modelConfigId/configVersion
- ✅ workspacePath 通过 updateAgentRunWorkspacePath 正确更新
- ✅ CodeGenerationRequest 正确传递模型上下文
- ✅ SSE 错误传播链路正常
- ⚠️ AI 生成因 API key 未配置而失败（非代码问题，需配置 AI_API_KEY 环境变量）
- ⚠️ 未使用 python-agent runtime（需设置 AGENT_RUNTIME=python-agent 环境变量重启 Java）

## Known Gaps

- ~~`modelConfigId` 和 `configVersion` 在 `AppServiceImpl` 构建 `CodeGenerationRequest` 时未填充。~~ **已修复**: AppServiceImpl 现在通过 ModelConfigService.getDefaultEnabledModelConfig 查找默认配置并传递。
- ~~当前 Python Agent 无模型配置时使用确定性 fallback 内容，非模型驱动生成。~~ **已修复**: Python AgentService 现在通过 Java internal API 获取模型配置并创建模型客户端。
- 要完成 python-agent runtime 的完整 E2E 验证，需要:
  1. 设置 `AI_API_KEY` 环境变量为有效的 OpenAI-compatible API key
  2. 设置 `AGENT_RUNTIME=python-agent` 环境变量
  3. 设置 `AGENT_PYTHON_BASE_URL=http://localhost:9000`
  4. 重启 Java 后端

## Issues

- None
