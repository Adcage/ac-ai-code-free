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


def route_after_route_step(state: AgentLoopState) -> str:
    """route_step 完成后，根据 route_decision 或 status 路由。"""
    if _get_state_attr(state, "status") == "waiting_for_user":
        return "finish"
    if _get_state_attr(state, "status") in ("completed", "failed"):
        return "finish"
    decision = _get_state_attr(state, "route_decision")
    if decision and isinstance(decision, dict):
        mode = decision.get("mode", "plan")
        if mode == "finish":
            return "finish"
        if mode == "plan":
            return "plan_step"
        if mode == "implement":
            return "implement_step"
        if mode == "validate":
            return "validate_step"
    # 默认路由到 plan
    return "plan_step"


def route_after_step(state: AgentLoopState) -> str:
    """plan_step 完成后的路由逻辑（沿用原有逻辑）。"""
    if _get_state_attr(state, "status") == "waiting_for_user":
        return "finish"
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
        return "implement_step"
    mode = _get_state_attr(state, "mode")
    if mode == "plan":
        return "plan_step"
    if mode == "implement":
        return "implement_step"
    return "finish"


def build_agent_loop_graph(
    init_node,
    route_step_node,
    plan_step_node,
    implement_step_node,
    validate_step_node,
    finish_node,
) -> StateGraph:
    """构建 Agent Loop 图结构。

    图结构：
        init → route_step → [plan_step / implement_step / validate_step / finish]

        大循环内：
          plan_step ↔ implement_step → route_step → [validate_step / finish]
          validate_step → route_step → [implement_step(修复) / finish]
    """
    graph = StateGraph(AgentLoopState)

    graph.add_node("init", init_node)
    graph.add_node("route_step", route_step_node)
    graph.add_node("plan_step", plan_step_node)
    graph.add_node("implement_step", implement_step_node)
    graph.add_node("validate_step", validate_step_node)
    graph.add_node("finish", finish_node)

    graph.set_entry_point("init")
    graph.add_edge("init", "route_step")

    # route_step 的条件边：根据 route_decision 路由
    graph.add_conditional_edges(
        "route_step",
        route_after_route_step,
        {
            "plan_step": "plan_step",
            "implement_step": "implement_step",
            "validate_step": "validate_step",
            "finish": "finish",
        },
    )

    # plan_step 条件边
    graph.add_conditional_edges(
        "plan_step",
        route_after_step,
        {"plan_step": "plan_step", "implement_step": "implement_step", "finish": "finish"},
    )

    # implement_step 完成后标记并路由到 route_step
    # 注意：这里需要在 implement_step 完成后设置 implement_just_finished = True
    # 实际由 ImplementStepNode 在 _execute_single_step 返回后处理
    graph.add_edge("implement_step", "route_step")

    # validate_step 完成后路由到 route_step
    graph.add_edge("validate_step", "route_step")

    return graph.compile()
