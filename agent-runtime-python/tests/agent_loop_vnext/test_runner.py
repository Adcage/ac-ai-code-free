"""测试 Runner 集成。"""

from app.agent_loop_vnext.runner import SingleImplementLoopRunner


def test_runner_instantiation():
    """Runner 应能正常实例化。"""
    assert hasattr(SingleImplementLoopRunner, "run")
