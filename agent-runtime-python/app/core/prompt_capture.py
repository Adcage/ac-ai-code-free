import functools
import json
import logging
import os
import time as time_mod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

from app.core.config import settings

logger = logging.getLogger("app.core.prompt_capture")


@dataclass
class CaptureStep:
    mode: str = ""
    iteration: int = 0
    model: str = ""
    tool_count: int = 0
    tool_names: list[str] = field(default_factory=list)
    system_prompt: str = ""
    user_prompt: str = ""
    conversation_messages: list[dict[str, Any]] = field(default_factory=list)
    response_text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: str = ""


@dataclass
class EnhanceRecord:
    model: str = ""
    original_prompt: str = ""
    enhanced_prompt: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""


class PromptCapture:
    def __init__(self, agent_run_id: int, code_gen_type: str = "", run_mode: str = ""):
        self._enabled = settings.prompt_capture_enabled
        self._agent_run_id = agent_run_id
        self._code_gen_type = code_gen_type
        self._run_mode = run_mode
        self._timestamp = datetime.now(timezone.utc).isoformat()
        self._user_prompt: str = ""
        self._steps: list[CaptureStep] = []
        self._enhance: EnhanceRecord | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_user_prompt(self, prompt: str) -> None:
        self._user_prompt = prompt

    def record_step(self, step: CaptureStep) -> None:
        if not self._enabled:
            return
        self._steps.append(step)

    def record_enhance(self, record: EnhanceRecord) -> None:
        if not self._enabled:
            return
        self._enhance = record

    async def save(self) -> str | None:
        if not self._enabled:
            return None

        base_dir = Path(settings.prompt_capture_dir)
        if not base_dir.is_absolute():
            project_root = Path(os.environ.get("AGENT_RUNTIME_ROOT", Path.cwd()))
            base_dir = project_root / base_dir

        output_dir = base_dir / str(self._agent_run_id)
        output_dir.mkdir(parents=True, exist_ok=True)

        chain_entries = []
        for i, step in enumerate(self._steps):
            seq = i + 1
            filename = f"{seq:02d}_{step.mode}_step_iter_{step.iteration}.md"
            filepath = output_dir / filename
            await self._write_step_md(filepath, step)
            chain_entries.append({
                "seq": seq,
                "mode": step.mode,
                "iteration": step.iteration,
                "model": step.model,
                "tool_count": step.tool_count,
                "file": filename,
            })

        enhance_entry = None
        if self._enhance is not None:
            enhance_path = output_dir / "enhance_prompt.md"
            await self._write_enhance_md(enhance_path, self._enhance)
            enhance_entry = {
                "model": self._enhance.model,
                "original_length": len(self._enhance.original_prompt),
                "enhanced_length": len(self._enhance.enhanced_prompt),
                "file": "enhance_prompt.md",
            }

        index_data = {
            "agent_run_id": self._agent_run_id,
            "timestamp": self._timestamp,
            "code_gen_type": self._code_gen_type,
            "run_mode": self._run_mode,
            "user_prompt": self._user_prompt,
            "total_iterations": len(self._steps),
            "chain": chain_entries,
        }
        if enhance_entry is not None:
            index_data["enhance_prompt"] = enhance_entry

        index_path = output_dir / "index.json"
        async with aiofiles.open(index_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(index_data, ensure_ascii=False, indent=2))

        logger.info(
            "prompt_capture saved | dir=%s steps=%d",
            output_dir,
            len(self._steps),
        )
        return str(output_dir)

    async def _write_step_md(self, filepath: Path, step: CaptureStep) -> None:
        mode_label = "Plan" if step.mode == "plan" else "Implement"
        lines = [
            f"# {mode_label} Step — Iteration {step.iteration}",
            "",
            f"**Model:** {step.model} | **Tools:** {step.tool_count} | **Time:** {step.timestamp}",
            "",
            "---",
            "",
            f"## System Prompt ({len(step.system_prompt)} 字符)",
            "",
            "<details>",
            "<summary>展开完整内容</summary>",
            "",
            step.system_prompt,
            "",
            "</details>",
            "",
            "---",
            "",
            f"## User Message ({len(step.user_prompt)} 字符)",
            "",
            step.user_prompt,
            "",
        ]

        if step.conversation_messages:
            lines.append("---")
            lines.append("")
            lines.append("## Conversation History")
            lines.append("")
            for msg in step.conversation_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"**{role}:** ({len(content)} 字符)")
                lines.append("")
                lines.append("<details>")
                lines.append("<summary>展开</summary>")
                lines.append("")
                lines.append(content)
                lines.append("")
                lines.append("</details>")
                lines.append("")
        else:
            lines.append("---")
            lines.append("")
            lines.append("## Conversation History")
            lines.append("")
            lines.append("（无历史消息）")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Model Response")
        lines.append("")
        if step.duration_ms > 0:
            lines.append(f"**Duration:** {step.duration_ms:.0f}ms")
            lines.append("")

        if step.response_text:
            lines.append(f"### Text ({len(step.response_text)} 字符)")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>展开完整内容</summary>")
            lines.append("")
            lines.append(step.response_text)
            lines.append("")
            lines.append("</details>")
            lines.append("")

        if step.tool_calls:
            lines.append(f"### Tool Calls ({len(step.tool_calls)})")
            lines.append("")
            lines.append("| # | Tool | Arguments | Result |")
            lines.append("|---|------|-----------|--------|")
            for j, tc in enumerate(step.tool_calls):
                name = tc.get("name", "")
                args_str = json.dumps(tc.get("arguments", {}), ensure_ascii=False)
                if len(args_str) > 200:
                    args_str = args_str[:200] + "..."
                result_str = ""
                if j < len(step.tool_results):
                    tr = step.tool_results[j]
                    if tr.get("error"):
                        result_str = f"ERROR: {tr['error'][:100]}"
                    elif tr.get("result"):
                        result_str = tr["result"][:100]
                lines.append(f"| {j + 1} | `{name}` | `{args_str}` | `{result_str}` |")
            lines.append("")

        content = "\n".join(lines)
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)

    async def _write_enhance_md(self, filepath: Path, record: EnhanceRecord) -> None:
        lines = [
            "# Enhance Prompt",
            "",
            f"**Model:** {record.model} | **Time:** {record.timestamp}",
            "",
            "---",
            "",
            f"## Original Prompt ({len(record.original_prompt)} 字符)",
            "",
            record.original_prompt,
            "",
            "---",
            "",
            f"## Enhanced Prompt ({len(record.enhanced_prompt)} 字符)",
            "",
            record.enhanced_prompt,
            "",
            "---",
            "",
            "## LLM Messages",
            "",
        ]
        for msg in record.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"### {role} ({len(content)} 字符)")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>展开</summary>")
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("</details>")
            lines.append("")

        content = "\n".join(lines)
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)


def capture_llm_call(func):
    @functools.wraps(func)
    async def wrapper(state, context, services, system_prompt, lc_tools, tool_handlers, file_tools):
        capture = getattr(state, "_prompt_capture", None)
        step_before: CaptureStep | None = None

        if capture and capture.enabled:
            step_before = CaptureStep(
                mode=state.mode,
                iteration=state.iteration + 1,
                model=state.resolved_model.get("modelName", "") if state.resolved_model else "",
                tool_count=len(lc_tools),
                tool_names=[getattr(t, "name", str(t)) for t in lc_tools],
                system_prompt=system_prompt,
                user_prompt=context.prompt,
                conversation_messages=[
                    {"role": m.get("role", "unknown"), "content": m.get("content", "")}
                    for m in state.conversation_messages
                ],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        start_ms = time_mod.monotonic()
        result = await func(state, context, services, system_prompt, lc_tools, tool_handlers, file_tools)
        duration_ms = (time_mod.monotonic() - start_ms) * 1000

        if capture and capture.enabled and step_before is not None:
            step_before.duration_ms = duration_ms
            step_before.response_text = getattr(result, "model_response_text", "")
            executed = getattr(result, "executed_tool_calls", [])
            step_before.tool_calls = [
                {"name": tc.name, "arguments": tc.arguments}
                for tc in executed
                if hasattr(tc, "name") and hasattr(tc, "arguments")
            ]
            step_before.tool_results = [
                {
                    "name": tc.name,
                    "result": tc.result if hasattr(tc, "result") and tc.result else "",
                    "error": tc.error if hasattr(tc, "error") and tc.error else "",
                }
                for tc in executed
                if hasattr(tc, "name")
            ]
            capture.record_step(step_before)

        return result

    return wrapper
