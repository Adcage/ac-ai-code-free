import logging
from typing import Any

from app.capabilities.skills.types import SkillDefinition
from app.prompts.modules import PromptModule

logger = logging.getLogger("app.capabilities.skills.prompt_module")


class SelectedSkillModule(PromptModule):
    id = "selected_skill"

    def enabled(self, context: Any, state: Any) -> bool:
        caps = getattr(state, "selected_capabilities", None)
        if caps is None:
            return False
        return getattr(caps, "skill", None) is not None

    def render(self, context: Any, state: Any) -> str:
        caps = getattr(state, "selected_capabilities", None)
        if caps is None:
            return ""
        skill: SkillDefinition | None = getattr(caps, "skill", None)
        if skill is None:
            return ""

        sections: list[str] = []
        sections.append(f"## Selected Skill: {skill.name}")
        sections.append("")
        sections.append("Use this workflow for the current generation.")
        sections.append("")
        sections.append(skill.body.strip())

        if skill.preview is not None:
            sections.append("")
            sections.append("Preview target:")
            sections.append(f"- type: {skill.preview.type}")
            sections.append(f"- entry: {skill.preview.entry}")

        return "\n".join(sections)
