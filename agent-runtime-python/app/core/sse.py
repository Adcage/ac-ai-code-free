import json

from app.events.agent_event import AgentEvent


def format_sse(event: AgentEvent) -> str:
    payload = json.dumps(event.model_dump(), ensure_ascii=False)
    return f"event: {event.eventType}\ndata: {payload}\n\n"
