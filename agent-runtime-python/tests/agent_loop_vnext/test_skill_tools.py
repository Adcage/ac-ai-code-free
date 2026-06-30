"""LoadSkillTool 和 ReadTool skill/ 前缀解析测试。"""

import os
import tempfile

import pytest

from app.agent_loop_vnext.shared.tools.skill_tools import LoadSkillTool
from app.agent_loop_vnext.state import LoadedSkill, SingleImplementState
from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.skills.types import SkillDefinition
from app.core.exceptions import AgentRuntimeError


# --- Fixtures ---


def _make_skill_def(skill_id: str, name: str, description: str = "", body: str = "", refs: tuple[str, ...] = ()) -> SkillDefinition:
    """构造测试用 SkillDefinition。"""
    from pathlib import Path
    return SkillDefinition(
        id=skill_id,
        name=name,
        description=description,
        body=body or f"# {name}\n这是 {name} 技能的正文。",
        source_path=Path(f"/fake/skills/{skill_id}/SKILL.md"),
        references=refs,
    )


def _make_registry(*skills: SkillDefinition) -> SkillRegistry:
    """构造包含指定 skills 的 SkillRegistry。"""
    registry = SkillRegistry()
    for skill in skills:
        registry.register(skill)
    return registry


# --- LoadSkillTool Tests ---


class TestLoadSkillTool:
    @pytest.mark.asyncio
    async def test_load_skill_loads_main_file(self):
        """加载后 state.loaded_skills 有值。"""
        skill_def = _make_skill_def("landing-page", "Landing Page", "制作落地页")
        registry = _make_registry(skill_def)
        state = SingleImplementState()
        tool = LoadSkillTool(skill_registry=registry, state=state)

        result = await tool._arun(skill_id="landing-page")

        assert "landing-page" in state.loaded_skills
        loaded = state.loaded_skills["landing-page"]
        assert loaded.skill_id == "landing-page"
        assert loaded.name == "Landing Page"
        assert "Landing Page" in result  # 正文包含技能名

    @pytest.mark.asyncio
    async def test_load_skill_returns_body_and_references(self):
        """返回正文和参考文件列表（带 skill/ 前缀）。"""
        skill_def = _make_skill_def(
            "web-prototype", "Web Prototype",
            refs=("references/layouts.md", "references/checklist.md"),
        )
        registry = _make_registry(skill_def)
        state = SingleImplementState()
        tool = LoadSkillTool(skill_registry=registry, state=state)

        result = await tool._arun(skill_id="web-prototype")

        assert "Web Prototype" in result
        assert "skill/web-prototype/references/layouts.md" in result
        assert "skill/web-prototype/references/checklist.md" in result

    @pytest.mark.asyncio
    async def test_load_skill_rejects_unknown_skill(self):
        """未知 skill_id 抛 SKILL_RESOURCE_NOT_FOUND。"""
        registry = _make_registry()
        state = SingleImplementState()
        tool = LoadSkillTool(skill_registry=registry, state=state)

        with pytest.raises(AgentRuntimeError) as exc_info:
            await tool._arun(skill_id="nonexistent")
        assert exc_info.value.code.name == "SKILL_RESOURCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_load_skill_idempotent(self):
        """重复加载同一 skill_id 返回"已加载"提示，不报错。"""
        skill_def = _make_skill_def("landing-page", "Landing Page")
        registry = _make_registry(skill_def)
        state = SingleImplementState()
        tool = LoadSkillTool(skill_registry=registry, state=state)

        result1 = await tool._arun(skill_id="landing-page")
        result2 = await tool._arun(skill_id="landing-page")

        assert "已加载" in result2
        # state 中仍然只有一个
        assert len(state.loaded_skills) == 1

    @pytest.mark.asyncio
    async def test_load_skill_multiple_skills(self):
        """可加载多个不同 skill。"""
        skill_a = _make_skill_def("landing-page", "Landing Page")
        skill_b = _make_skill_def("dashboard", "Dashboard")
        registry = _make_registry(skill_a, skill_b)
        state = SingleImplementState()
        tool = LoadSkillTool(skill_registry=registry, state=state)

        await tool._arun(skill_id="landing-page")
        await tool._arun(skill_id="dashboard")

        assert len(state.loaded_skills) == 2
        assert "landing-page" in state.loaded_skills
        assert "dashboard" in state.loaded_skills

    @pytest.mark.asyncio
    async def test_load_skill_no_references(self):
        """无参考文件的 Skill 不列出参考文件部分。"""
        skill_def = _make_skill_def("simple-skill", "Simple Skill", refs=())
        registry = _make_registry(skill_def)
        state = SingleImplementState()
        tool = LoadSkillTool(skill_registry=registry, state=state)

        result = await tool._arun(skill_id="simple-skill")

        assert "可用参考文件" not in result
        assert "Simple Skill" in result


# --- ReadTool skill/ prefix Tests ---


class TestReadSkillPrefix:
    @pytest.mark.asyncio
    async def test_read_skill_prefix_resolves(self):
        """skill/{id}/xxx 路径正确解析到 Skill 目录下的文件。"""
        from app.agent_loop_vnext.shared.tools.file_tools import ReadTool
        from app.tools.file_tools import FileTools, Workspace

        # 创建临时 Skill 目录和文件
        with tempfile.TemporaryDirectory() as skill_dir:
            ref_file = os.path.join(skill_dir, "references", "guide.md")
            os.makedirs(os.path.dirname(ref_file), exist_ok=True)
            with open(ref_file, "w", encoding="utf-8") as f:
                f.write("# Guide\nThis is a guide.")

            # 设置 state
            state = SingleImplementState()
            state.loaded_skills["test-skill"] = LoadedSkill(
                skill_id="test-skill",
                name="Test Skill",
                description="Test",
                source_dir=os.path.abspath(skill_dir),
                references=("references/guide.md",),
            )

            # 创建工具
            with tempfile.TemporaryDirectory() as workspace_dir:
                workspace = Workspace(workspace_dir)
                file_tools = FileTools(workspace)
                tool = ReadTool(file_tools=file_tools, state=state)

                result = await tool._arun(path="skill/test-skill/references/guide.md")
                assert "This is a guide." in result

    @pytest.mark.asyncio
    async def test_read_skill_prefix_traversal_blocked(self):
        """skill/{id}/../../etc/passwd 路径穿越被拦截。"""
        from app.agent_loop_vnext.shared.tools.file_tools import ReadTool
        from app.tools.file_tools import FileTools, Workspace

        with tempfile.TemporaryDirectory() as skill_dir:
            state = SingleImplementState()
            state.loaded_skills["test-skill"] = LoadedSkill(
                skill_id="test-skill",
                name="Test Skill",
                description="Test",
                source_dir=os.path.abspath(skill_dir),
                references=(),
            )

            with tempfile.TemporaryDirectory() as workspace_dir:
                workspace = Workspace(workspace_dir)
                file_tools = FileTools(workspace)
                tool = ReadTool(file_tools=file_tools, state=state)

                with pytest.raises(AgentRuntimeError) as exc_info:
                    await tool._arun(path="skill/test-skill/../../etc/passwd")
                assert exc_info.value.code.name == "PATH_TRAVERSAL_BLOCKED"

    @pytest.mark.asyncio
    async def test_read_skill_prefix_unknown_skill(self):
        """未加载的 skill_id 报 SKILL_RESOURCE_NOT_FOUND。"""
        from app.agent_loop_vnext.shared.tools.file_tools import ReadTool
        from app.tools.file_tools import FileTools, Workspace

        state = SingleImplementState()  # 无 loaded_skills

        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Workspace(workspace_dir)
            file_tools = FileTools(workspace)
            tool = ReadTool(file_tools=file_tools, state=state)

            with pytest.raises(AgentRuntimeError) as exc_info:
                await tool._arun(path="skill/unknown-skill/guide.md")
            assert exc_info.value.code.name == "SKILL_RESOURCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_read_skill_prefix_no_state(self):
        """state 为 None 时使用 skill/ 前缀报错。"""
        from app.agent_loop_vnext.shared.tools.file_tools import ReadTool
        from app.tools.file_tools import FileTools, Workspace

        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Workspace(workspace_dir)
            file_tools = FileTools(workspace)
            tool = ReadTool(file_tools=file_tools, state=None)

            with pytest.raises(AgentRuntimeError) as exc_info:
                await tool._arun(path="skill/some-skill/guide.md")
            assert exc_info.value.code.name == "SKILL_RESOURCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_read_workspace_path_unchanged(self):
        """无前缀时走 workspace 逻辑不变。"""
        from app.agent_loop_vnext.shared.tools.file_tools import ReadTool
        from app.tools.file_tools import FileTools, Workspace

        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Workspace(workspace_dir)
            file_tools = FileTools(workspace)
            # 创建一个文件
            test_file = os.path.join(workspace_dir, "test.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("hello workspace")

            state = SingleImplementState()
            tool = ReadTool(file_tools=file_tools, state=state)

            result = await tool._arun(path="test.txt")
            assert "hello workspace" in result

    @pytest.mark.asyncio
    async def test_read_skill_prefix_suggests_correct_path(self):
        """文件不存在且匹配已加载 Skill 参考文件时，提示正确前缀路径。"""
        from app.agent_loop_vnext.shared.tools.file_tools import ReadTool
        from app.tools.file_tools import FileTools, Workspace

        state = SingleImplementState()
        state.loaded_skills["web-prototype"] = LoadedSkill(
            skill_id="web-prototype",
            name="Web Prototype",
            description="Test",
            source_dir="/fake/skills/web-prototype",
            references=("references/layouts.md",),
        )

        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Workspace(workspace_dir)
            file_tools = FileTools(workspace)
            tool = ReadTool(file_tools=file_tools, state=state)

            with pytest.raises(AgentRuntimeError) as exc_info:
                await tool._arun(path="layouts.md")
            # 错误信息应包含正确的 skill/ 前缀提示
            assert "skill/web-prototype/references/layouts.md" in str(exc_info.value)
