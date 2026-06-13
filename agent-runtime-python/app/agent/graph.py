import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.agent.state import AgentState
from app.events.agent_event import AgentEvent
from app.schemas.code_generation import CodeGenerationRequest
from app.services.prompt_builder import PromptBuilder
from app.tools.file_tools import FileTools
from app.tools.workspace import Workspace

prompt_builder = PromptBuilder()

_FALLBACK_CONTENT = "<template><main><h1>AI Generated App</h1></main></template>\n"

_VUE_PROJECT_STATIC_FILES = {
    "package.json": """{
  "name": "ai-generated-vue-app",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0"
  },
  "dependencies": {
    "vue": "^3.5.18"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.4",
    "vite": "^5.4.19"
  }
}
""",
    "index.html": """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Generated App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
""",
    "vite.config.js": """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
})
""",
    "src/main.js": """import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
""",
}


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:vue|html)?\s*\n?", "", text)
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text.strip()


def _build_files(request: CodeGenerationRequest, generated_content: str) -> list[tuple[str, str]]:
    if request.codeGenType != "vue_project":
        return [("src/App.vue", generated_content)]
    return [
        *_VUE_PROJECT_STATIC_FILES.items(),
        ("src/App.vue", generated_content),
    ]


async def invoke_model(state: AgentState) -> AgentState:
    request = state["request"]
    events = list(state["events"])
    seq = len(events) + 1
    chat_model = state.get("chat_model")

    if chat_model is None:
        events.append(AgentEvent(
            agentRunId=request.agentRunId, seq=seq, eventType="ai_response",
            data={"text": "已生成 Vue 页面源码（降级模板），准备写入 src/App.vue", "fallback": True},
        ))
        return {
            "request": request, "events": events,
            "model_config": state.get("model_config"), "chat_model": None,
            "generated_content": _FALLBACK_CONTENT, "error": None,
            "grpc_tool_client": state.get("grpc_tool_client"),
            "grpc_platform_client": state.get("grpc_platform_client"),
        }

    system_prompt = prompt_builder.build_vue_app_prompt(request.prompt)
    response: AIMessage = await chat_model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=request.prompt),
    ])
    content = _strip_markdown_fences(response.content or "")

    if not content:
        events.append(AgentEvent(
            agentRunId=request.agentRunId, seq=seq, eventType="error",
            data={"message": "模型返回内容为空"},
        ))
        return {
            "request": request, "events": events,
            "model_config": state.get("model_config"), "chat_model": chat_model,
            "generated_content": None, "error": "模型返回内容为空",
            "grpc_tool_client": state.get("grpc_tool_client"),
            "grpc_platform_client": state.get("grpc_platform_client"),
        }

    events.append(AgentEvent(
        agentRunId=request.agentRunId, seq=seq, eventType="ai_response",
        data={"text": "已生成 Vue 页面源码，准备写入 src/App.vue"},
    ))

    return {
        "request": request, "events": events,
        "model_config": state.get("model_config"), "chat_model": chat_model,
        "generated_content": content, "error": None,
        "grpc_tool_client": state.get("grpc_tool_client"),
        "grpc_platform_client": state.get("grpc_platform_client"),
    }


async def write_file(state: AgentState) -> AgentState:
    request = state["request"]
    events = list(state["events"])
    seq = len(events) + 1
    generated_content = state.get("generated_content")
    tool_client = state.get("grpc_tool_client")

    if generated_content is None:
        events.append(AgentEvent(
            agentRunId=request.agentRunId, seq=seq, eventType="error",
            data={"message": "无生成内容，跳过文件写入"},
        ))
        return {
            "request": request, "events": events,
            "model_config": state.get("model_config"), "chat_model": state.get("chat_model"),
            "generated_content": None, "error": state.get("error") or "无生成内容",
            "grpc_tool_client": tool_client, "grpc_platform_client": state.get("grpc_platform_client"),
        }

    files = _build_files(request, generated_content)
    workspace = None
    tools = None
    if not tool_client:
        workspace = Workspace(request.workspacePath or f"storage/agent-workspaces/{request.agentRunId}/source")
        tools = FileTools(workspace)

    for index, (path, content) in enumerate(files, start=1):
        tool_id = f"tool-{index}"
        events.append(AgentEvent(
            agentRunId=request.agentRunId, seq=seq, eventType="tool_request",
            data={"id": tool_id, "name": "write_file", "arguments": {"path": path}},
        ))
        seq += 1

        if tool_client:
            result = await tool_client.write_file(path, content)
        else:
            result = tools.write_file(path, content)

        events.append(AgentEvent(
            agentRunId=request.agentRunId, seq=seq, eventType="tool_executed",
            data={"id": tool_id, "name": "write_file", "arguments": {"path": path}, "result": result},
        ))
        seq += 1

    events.append(AgentEvent(agentRunId=request.agentRunId, seq=seq, eventType="done", data={"message": "completed"}))
    return {
        "request": request, "events": events,
        "model_config": state.get("model_config"), "chat_model": state.get("chat_model"),
        "generated_content": generated_content, "error": None,
        "grpc_tool_client": tool_client, "grpc_platform_client": state.get("grpc_platform_client"),
    }


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("invoke_model", invoke_model)
    graph.add_node("write_file", write_file)
    graph.set_entry_point("invoke_model")
    graph.add_edge("invoke_model", "write_file")
    graph.add_edge("write_file", END)
    return graph.compile()
