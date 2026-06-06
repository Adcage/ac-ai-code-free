from langgraph.graph import END, StateGraph

from app.agent.state import AgentState
from app.events.agent_event import AgentEvent
from app.tools.file_tools import FileTools
from app.tools.workspace import Workspace


def write_minimal_project(state: AgentState) -> AgentState:
    request = state["request"]
    events = list(state["events"])
    seq = len(events) + 1
    workspace = Workspace(request.workspacePath or f"storage/agent-workspaces/{request.agentRunId}/source")
    tools = FileTools(workspace)
    path = "src/App.vue"
    content = "<template><main><h1>AI Generated App</h1></main></template>\n"

    events.append(AgentEvent(
        agentRunId=request.agentRunId, seq=seq, eventType="tool_request",
        data={"id": "tool-1", "name": "write_file", "arguments": {"path": path}},
    ))
    seq += 1

    result = tools.write_file(path, content)
    events.append(AgentEvent(
        agentRunId=request.agentRunId, seq=seq, eventType="tool_executed",
        data={"id": "tool-1", "name": "write_file", "arguments": {"path": path}, "result": result},
    ))
    seq += 1

    events.append(AgentEvent(agentRunId=request.agentRunId, seq=seq, eventType="done", data={"message": "completed"}))
    return {"request": request, "events": events}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("write_minimal_project", write_minimal_project)
    graph.set_entry_point("write_minimal_project")
    graph.add_edge("write_minimal_project", END)
    return graph.compile()
