"""vNext Skill 工具集：load_skill。"""

import logging

from pydantic import BaseModel, Field

from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.agent_loop_vnext.state import LoadedSkill, SingleImplementState
from app.capabilities.skills.registry import SkillRegistry

logger = logging.getLogger("app.agent_loop_vnext.shared.tools.skill_tools")


class LoadSkillInput(BaseModel):
    skill_id: str = Field(description="要加载的技能 ID，例如 landing-page、web-prototype")


class LoadSkillTool(AgentTool):
    name: str = "load_skill"
    description: str = "加载指定技能的规则和参考文件列表。加载后可通过 Read 工具使用 skill/{skill_id}/ 路径前缀读取参考文件。"
    args_schema: type = LoadSkillInput
    skill_registry: SkillRegistry | None = None
    state: SingleImplementState | None = None

    async def _arun(self, skill_id: str) -> str:
        from app.core.error_codes import AgentErrorCode
        from app.core.exceptions import AgentRuntimeError

        if self.skill_registry is None or self.state is None:
            raise AgentRuntimeError(
                "Skill 系统未初始化", code=AgentErrorCode.SKILL_RESOURCE_NOT_FOUND
            )

        # 已加载 → 返回提示
        if skill_id in self.state.loaded_skills:
            existing = self.state.loaded_skills[skill_id]
            return f"技能 {skill_id} 已加载，无需重复加载。\n\n{existing.description}"

        # 从注册表获取
        try:
            skill_def = self.skill_registry.get(skill_id)
        except KeyError:
            raise AgentRuntimeError(
                f"未找到技能: {skill_id}",
                code=AgentErrorCode.SKILL_RESOURCE_NOT_FOUND,
            )

        # 构造 LoadedSkill 并写入 state
        import os

        source_dir = str(skill_def.source_path.parent)
        loaded = LoadedSkill(
            skill_id=skill_def.id,
            name=skill_def.name,
            description=skill_def.description,
            source_dir=os.path.abspath(source_dir),
            references=skill_def.references,
        )
        self.state.loaded_skills[skill_id] = loaded

        logger.info("load_skill | skill_id=%s refs=%d", skill_id, len(loaded.references))

        # 构造返回内容：正文 + 参考文件列表
        parts = [skill_def.body]

        if loaded.references:
            parts.append("\n## 可用参考文件")
            parts.append("使用 Read 工具读取，路径前缀为 skill/{skill_id}/：")
            for ref in loaded.references:
                parts.append(f"- skill/{skill_id}/{ref}")

        return "\n".join(parts)
