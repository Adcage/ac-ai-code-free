from collections.abc import AsyncIterator

from app.agent.graph import build_graph
from app.events.agent_event import AgentEvent
from app.schemas.code_generation import CodeGenerationRequest


class AgentService:
    def __init__(self):
        self.graph = build_graph()

    async def stream(self, request: CodeGenerationRequest) -> AsyncIterator[AgentEvent]:
        start = AgentEvent(agentRunId=request.agentRunId, seq=1, eventType="agent_start", data={"runtime": "python-langgraph"})
        yield start
        result = await self.graph.ainvoke({"request": request, "events": [start]})
        for event in result["events"][1:]:
            yield event
