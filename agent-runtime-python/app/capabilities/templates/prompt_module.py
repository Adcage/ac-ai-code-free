import logging
from pathlib import Path

from app.capabilities.templates.types import TemplateDefinition
from app.prompts.modules import PromptModule

logger = logging.getLogger("app.capabilities.templates.prompt_module")

DEFAULT_FILE_MAX_CHARS = 4000


class TemplateReferenceModule(PromptModule):
    id = "template_reference"

    def __init__(self, file_max_chars: int = DEFAULT_FILE_MAX_CHARS) -> None:
        self._file_max_chars = file_max_chars

    def enabled(self, context: object, state: object) -> bool:
        caps = getattr(state, "selected_capabilities", None)
        if caps is None:
            return False
        return getattr(caps, "template", None) is not None

    def render(self, context: object, state: object) -> str:
        caps = getattr(state, "selected_capabilities", None)
        if caps is None:
            return ""
        template: TemplateDefinition | None = getattr(caps, "template", None)
        if template is None:
            return ""

        sections: list[str] = []
        sections.append(f"## Reference Template: {template.name}")
        sections.append("")
        sections.append(
            "Use this as a structure reference. Adapt content, labels, states, "
            "and styling to the user's request and the active design system."
        )

        files_to_inject = template.files[: template.max_prompt_files]
        for file_path in files_to_inject:
            resolved = template.source_path.parent / file_path
            content = self._read_file(resolved)
            if not content:
                continue

            if len(content) > self._file_max_chars:
                content = content[: self._file_max_chars] + "\n... [truncated]"

            sections.append("")
            sections.append(f"### {file_path}")
            sections.append("```")
            sections.append(content)
            sections.append("```")

        return "\n".join(sections)

    def _read_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to read template file %s: %s", path, e)
            return ""
