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

- Python health:
- Java startup:
- Frontend startup:
- SSE generation:
- Workspace file:
- Chat history:

## Known Gaps

- `modelConfigId` 和 `configVersion` 在 `AppServiceImpl` 构建 `CodeGenerationRequest` 时未填充。`app` 表无此列，`AgentRun` 实体有此字段但 `createAgentRun` 未接受这些参数。待后续从默认模型配置或前端请求参数补充。
- 当前 Python Agent 无模型配置时使用确定性 fallback 内容，非模型驱动生成。

## Issues

- None
