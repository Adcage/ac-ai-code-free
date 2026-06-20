from pathlib import Path

import pytest

from app.agent_loop.state import AgentLoopState
from app.agent_loop.tools.run_checks import RunChecksTool
from app.runtime.context import CodeGenType


class CapturingQualityChecker:
    def __init__(self):
        self.manifest = None

    def run(self, workspace_root, manifest):
        self.manifest = manifest
        return []


@pytest.mark.asyncio
async def test_run_checks_uses_injected_code_gen_type(tmp_path: Path):
    state = AgentLoopState(files_touched=["src/App.vue"])
    checker = CapturingQualityChecker()
    tool = RunChecksTool()
    tool.set_state(state)
    tool.set_workspace(str(tmp_path))
    tool.set_quality_checker(checker)
    tool.set_code_gen_type(CodeGenType.VUE_PROJECT)

    await tool._arun()

    assert checker.manifest is not None
    assert checker.manifest.code_gen_type == "vue_project"
    assert checker.manifest.entry == "src/App.vue"
