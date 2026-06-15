import pytest

from app.graph.workflow import WorkflowEngine
from app.nodes.base import NodeMetadata, RuntimeNode
from app.registries.node_registry import NodeRegistry
from app.runtime.context import CodeGenType, ExecutionContext, RunMode
from app.runtime.events import RuntimeEventType
from app.runtime.event_bus import EventBus
from app.runtime.services import RuntimeServices
from app.runtime.state import ExecutionState
from app.core.exceptions import AgentRuntimeError
from app.core.error_codes import AgentErrorCode


def _make_context() -> ExecutionContext:
    return ExecutionContext(
        agent_run_id=1,
        app_id=1,
        session_id=1,
        user_id=1,
        prompt="test",
        code_gen_type=CodeGenType.VUE_PROJECT,
        workspace_path="/tmp",
        run_mode=RunMode.GENERATE,
    )


class _RecordingNode(RuntimeNode):
    def __init__(self, node_id: str):
        self.metadata = NodeMetadata(id=node_id, name=node_id)
        self.calls: list[str] = []

    async def run(self, context, state, services):
        self.calls.append(context.prompt)
        return state


class _FailingNode(RuntimeNode):
    def __init__(self, node_id: str):
        self.metadata = NodeMetadata(id=node_id, name=node_id)

    async def run(self, context, state, services):
        raise AgentRuntimeError("boom", code=AgentErrorCode.INTERNAL_ERROR)


class _SkipNode(RuntimeNode):
    def __init__(self, node_id: str):
        self.metadata = NodeMetadata(id=node_id, name=node_id)

    def can_run(self, context, state) -> bool:
        return False

    async def run(self, context, state, services):
        return state


async def _run_workflow(definition, nodes, context=None):
    registry = NodeRegistry()
    for n in nodes:
        registry.register(n)
    engine = WorkflowEngine(registry)
    event_bus = EventBus(agent_run_id=1)
    services = RuntimeServices(event_bus=event_bus)
    ctx = context or _make_context()
    state = ExecutionState()
    result = await engine.execute(definition, ctx, state, services)
    await event_bus.close()
    return result, event_bus


class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_executes_nodes_in_order(self):
        n1 = _RecordingNode("a")
        n2 = _RecordingNode("b")
        state, _ = await _run_workflow(["a", "b"], [n1, n2])
        assert n1.calls == ["test"]
        assert n2.calls == ["test"]
        assert len(state.node_results) == 2
        assert state.node_results[0].node_id == "a"
        assert state.node_results[1].node_id == "b"

    @pytest.mark.asyncio
    async def test_skips_node_when_can_run_false(self):
        skip = _SkipNode("skip")
        ok = _RecordingNode("ok")
        state, _ = await _run_workflow(["skip", "ok"], [skip, ok])
        assert len(state.node_results) == 1
        assert state.node_results[0].node_id == "ok"

    @pytest.mark.asyncio
    async def test_critical_node_failure_terminates(self):
        fail = _FailingNode("call_model")
        ok = _RecordingNode("finalize")
        state, _ = await _run_workflow(["call_model", "finalize"], [fail, ok])
        assert len(state.errors) == 1
        assert len(state.node_results) == 1
        assert state.node_results[0].status == "error"

    @pytest.mark.asyncio
    async def test_non_critical_failure_continues(self):
        fail = _FailingNode("classify_task")
        ok = _RecordingNode("finalize")
        state, _ = await _run_workflow(["classify_task", "finalize"], [fail, ok])
        assert len(state.errors) == 1
        assert len(state.node_results) == 2

    @pytest.mark.asyncio
    async def test_emits_node_events(self):
        n1 = _RecordingNode("a")
        _, event_bus = await _run_workflow(["a"], [n1])
        events = []
        while True:
            e = await event_bus.next_event()
            if e is None:
                break
            events.append(e)
        event_types = [e.event.event_type for e in events]
        assert RuntimeEventType.NODE_STARTED in event_types
        assert RuntimeEventType.NODE_COMPLETED in event_types

    @pytest.mark.asyncio
    async def test_error_emits_runtime_error_event(self):
        fail = _FailingNode("call_model")
        _, event_bus = await _run_workflow(["call_model"], [fail])
        events = []
        while True:
            e = await event_bus.next_event()
            if e is None:
                break
            events.append(e)
        error_events = [e for e in events if e.event.event_type == RuntimeEventType.RUNTIME_ERROR]
        assert len(error_events) == 1
