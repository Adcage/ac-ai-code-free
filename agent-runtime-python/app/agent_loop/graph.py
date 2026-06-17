import logging

from langgraph.graph import StateGraph

from app.agent_loop.state import AgentLoopState

logger = logging.getLogger("app.agent_loop.graph")


def _get_state_attr(state, key, default=None):
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _set_state_attr(state, key, value):
    if isinstance(state, dict):
        state[key] = value
    else:
        setattr(state, key, value)


def route_after_step(state: AgentLoopState) -> str:
    if _get_state_attr(state, "status") in ("completed", "failed"):
        return "finish"
    if _get_state_attr(state, "iteration") >= _get_state_attr(state, "max_iterations"):
        return "finish"
    if _get_state_attr(state, "mode_switches") >= _get_state_attr(state, "max_mode_switches"):
        return "finish"
    if _get_state_attr(state, "mode") == "plan" and _get_state_attr(state, "plan_iterations") >= _get_state_attr(state, "max_plan_iterations"):
        logger.warning(
            "route | plan_iterations=%d exceeded max_plan_iterations=%d, force switching to implement",
            _get_state_attr(state, "plan_iterations"),
            _get_state_attr(state, "max_plan_iterations"),
        )
        _set_state_attr(state, "mode", "implement")
        return "implement"
    return _get_state_attr(state, "mode")


def build_agent_loop_graph(
    init_node,
    plan_step_node,
    implement_step_node,
    finish_node,
) -> StateGraph:
    graph = StateGraph(AgentLoopState)

    graph.add_node("init", init_node)
    graph.add_node("plan_step", plan_step_node)
    graph.add_node("implement_step", implement_step_node)
    graph.add_node("finish", finish_node)

    graph.set_entry_point("init")
    graph.add_edge("init", "plan_step")

    graph.add_conditional_edges(
        "plan_step",
        route_after_step,
        {"plan": "plan_step", "implement": "implement_step", "finish": "finish"},
    )
    graph.add_conditional_edges(
        "implement_step",
        route_after_step,
        {"plan": "plan_step", "implement": "implement_step", "finish": "finish"},
    )

    return graph.compile()
