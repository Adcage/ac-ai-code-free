from pydantic import BaseModel


class AgentEvent(BaseModel):
    agentRunId: str
    seq: int
    eventType: str
    data: dict
