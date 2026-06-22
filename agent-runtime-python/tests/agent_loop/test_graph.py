
from app.agent_loop.state import AgentLoopState
from app.agent_loop.graph import route_after_plan_step, route_after_route_step


class TestRouteAfterPlanStep:
    """测试 plan_step 完成后的路由逻辑。

    Plan 不再直接进入 Implement，而是：
    - plan_just_finished=True → route_step
    - waiting_for_user/completed/failed → finish
    - iteration 达到 max_iterations → finish
    - 否则 → plan_step
    """

    def test_continue_plan_without_finished_flag(self):
        state = AgentLoopState(mode="plan", status="running", iteration=1)
        assert route_after_plan_step(state) == "plan_step"

    def test_plan_just_finished_routes_to_route_step(self):
        state = AgentLoopState(mode="plan", status="running", plan_just_finished=True)
        assert route_after_plan_step(state) == "route_step"

    def test_finish_on_completed(self):
        state = AgentLoopState(status="completed")
        assert route_after_plan_step(state) == "finish"

    def test_finish_on_failed(self):
        state = AgentLoopState(status="failed")
        assert route_after_plan_step(state) == "finish"

    def test_finish_on_max_iterations(self):
        state = AgentLoopState(iteration=50, max_iterations=50)
        assert route_after_plan_step(state) == "finish"

    def test_finish_on_max_iterations_exceeded(self):
        state = AgentLoopState(iteration=51, max_iterations=50)
        assert route_after_plan_step(state) == "finish"

    def test_finish_on_max_mode_switches(self):
        state = AgentLoopState(mode_switches=6, max_mode_switches=6)
        assert route_after_plan_step(state) == "finish"

    def test_finish_on_max_mode_switches_exceeded(self):
        state = AgentLoopState(mode_switches=7, max_mode_switches=6)
        assert route_after_plan_step(state) == "finish"

    def test_plan_iterations_at_old_limit_stays_plan(self):
        state = AgentLoopState(mode="plan", status="running", plan_iterations=15, max_plan_iterations=15)
        result = route_after_plan_step(state)
        assert result == "plan_step"

    def test_plan_iterations_above_old_limit_stays_plan(self):
        state = AgentLoopState(mode="plan", status="running", plan_iterations=16, max_plan_iterations=15)
        result = route_after_plan_step(state)
        assert result == "plan_step"

    def test_plan_iterations_below_limit_stays_plan(self):
        state = AgentLoopState(mode="plan", status="running", plan_iterations=14, max_plan_iterations=15)
        assert route_after_plan_step(state) == "plan_step"

    def test_finish_on_waiting_for_user(self):
        state = AgentLoopState(status="waiting_for_user", iteration=3)
        assert route_after_plan_step(state) == "finish"


class TestRouteAfterRouteStep:
    """测试 route_step 完成后的路由逻辑。"""

    def test_route_to_plan(self):
        state = AgentLoopState(status="running", route_decided=True, route_decision={"mode": "plan"})
        assert route_after_route_step(state) == "plan_step"

    def test_route_to_implement(self):
        state = AgentLoopState(status="running", route_decided=True, route_decision={"mode": "implement"})
        assert route_after_route_step(state) == "implement_step"

    def test_route_to_validate(self):
        state = AgentLoopState(status="running", route_decided=True, route_decision={"mode": "validate"})
        assert route_after_route_step(state) == "validate_step"

    def test_route_to_finish(self):
        state = AgentLoopState(status="running", route_decided=True, route_decision={"mode": "finish"})
        assert route_after_route_step(state) == "finish"

    def test_route_to_finish_on_waiting_for_user(self):
        state = AgentLoopState(status="waiting_for_user", route_decided=False)
        assert route_after_route_step(state) == "finish"

    def test_route_to_finish_on_completed(self):
        state = AgentLoopState(status="completed", route_decided=False)
        assert route_after_route_step(state) == "finish"

    def test_default_route_to_plan(self):
        state = AgentLoopState(status="running", route_decided=False, route_decision=None)
        assert route_after_route_step(state) == "plan_step"
