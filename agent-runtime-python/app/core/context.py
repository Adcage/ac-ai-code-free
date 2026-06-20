from contextvars import ContextVar

trace_id: ContextVar[str] = ContextVar("trace_id", default="")
agent_run_id: ContextVar[str] = ContextVar("agent_run_id", default="")


def get_trace_id() -> str:
    return trace_id.get()


def set_trace_id(value: str) -> None:
    trace_id.set(value)


def get_agent_run_id() -> str:
    return agent_run_id.get()


def set_agent_run_id(value: str) -> None:
    agent_run_id.set(value)
