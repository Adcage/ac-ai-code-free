import json
import logging
from dataclasses import dataclass
from pathlib import Path

from app.capabilities.design_systems.types import DesignSystemDefinition
from app.prompts.modules import PromptModule

logger = logging.getLogger("app.capabilities.design_systems.prompt_module")

DEFAULT_DESIGN_MAX_CHARS = 6000
DEFAULT_TOKEN_SUMMARY_MAX_LINES = 120
DEFAULT_COMPONENTS_MAX_ENTRIES = 50


@dataclass(frozen=True)
class DesignSystemModuleConfig:
    design_max_chars: int = DEFAULT_DESIGN_MAX_CHARS
    token_summary_max_lines: int = DEFAULT_TOKEN_SUMMARY_MAX_LINES
    components_max_entries: int = DEFAULT_COMPONENTS_MAX_ENTRIES


class DesignSystemModule(PromptModule):
    id = "design_system"

    def __init__(self, config: DesignSystemModuleConfig | None = None) -> None:
        self._config = config or DesignSystemModuleConfig()

    def enabled(self, context: object, state: object) -> bool:
        caps = getattr(state, "selected_capabilities", None)
        if caps is None:
            return False
        return getattr(caps, "design_system", None) is not None

    def render(self, context: object, state: object) -> str:
        caps = getattr(state, "selected_capabilities", None)
        if caps is None:
            return ""
        ds: DesignSystemDefinition | None = getattr(caps, "design_system", None)
        if ds is None:
            return ""

        sections: list[str] = []
        sections.append(f"## Active Design System: {ds.name}")
        sections.append("")
        sections.append(
            "Follow this design system. It overrides generic visual preferences "
            "from the user prompt when they conflict."
        )

        design_content = self._read_file(ds.files.design)
        if design_content:
            truncated = self._truncate(design_content, self._config.design_max_chars)
            sections.append("")
            sections.append("### Design Rules")
            sections.append(truncated)

        token_summary = self._render_token_summary(ds.files.tokens)
        if token_summary:
            sections.append("")
            sections.append("### Token Summary")
            sections.append(token_summary)

        component_guidance = self._render_component_guidance(ds.files.components_manifest)
        if component_guidance:
            sections.append("")
            sections.append("### Component Guidance")
            sections.append(component_guidance)

        usage_rules = self._render_usage(ds.files.usage)
        if usage_rules:
            sections.append("")
            sections.append("### Usage Key Rules")
            sections.append(usage_rules)

        return "\n".join(sections)

    def _read_file(self, path: Path | None) -> str:
        if path is None:
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to read design system file %s: %s", path, e)
            return ""

    def _truncate(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n... (truncated)"

    def _render_token_summary(self, tokens_path: Path | None) -> str:
        if tokens_path is None:
            return ""
        content = self._read_file(tokens_path)
        if not content:
            return ""

        lines: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("--") and ":" in stripped:
                lines.append(f"- {stripped.rstrip(';')}")

        if not lines:
            return ""

        if len(lines) > self._config.token_summary_max_lines:
            lines = lines[: self._config.token_summary_max_lines]
            lines.append("... (more tokens omitted)")

        return "\n".join(lines)

    def _render_component_guidance(self, manifest_path: Path | None) -> str:
        if manifest_path is None:
            return ""
        content = self._read_file(manifest_path)
        if not content:
            return ""

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse components manifest: %s", manifest_path)
            return ""

        components = data.get("components")
        if not isinstance(components, list):
            return ""

        entries: list[str] = []
        for comp in components[: self._config.components_max_entries]:
            name = comp.get("name", "")
            desc = comp.get("description", "")
            if name:
                if desc:
                    entries.append(f"- {name}: {desc}")
                else:
                    entries.append(f"- {name}")

        if not entries:
            return ""

        return "\n".join(entries)

    def _render_usage(self, usage_path: Path | None) -> str:
        if usage_path is None:
            return ""
        content = self._read_file(usage_path)
        if not content:
            return ""
        return content.strip()
