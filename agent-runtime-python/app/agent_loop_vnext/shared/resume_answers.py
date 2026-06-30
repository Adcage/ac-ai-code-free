"""vNext resume 答案渲染 — 将 <<RESUME_ANSWERS>> 或 JSON 编码的答案转为 LLM 可读文本。

vNext 完全自包含，不依赖 legacy 引擎（app.agent_loop.resume_answers）。
支持两种格式：
1. <<RESUME_ANSWERS>>{JSON}<<RESUME_ANSWERS>> — 旧格式
2. {"type":"planning_resume","answers":{...}} — JSON 格式
"""

import json
import logging
import re

logger = logging.getLogger("app.agent_loop_vnext.resume_answers")

RESUME_MARKER = "<<RESUME_ANSWERS>>"
PLANNING_RESUME_TYPE = "planning_resume"


def render_resume_answer_text(prompt: str) -> str:
    """将编码的 resume 答案转为 LLM 可读文本。

    支持两种格式：
    - <<RESUME_ANSWERS>>{JSON}<<RESUME_ANSWERS>>（旧格式）
    - {"type":"planning_resume","answers":{...}}（JSON 格式）
    """
    if not prompt:
        return prompt

    # 检测 JSON 格式（新格式）
    if prompt.strip().startswith("{") and '"type":"planning_resume"' in prompt:
        try:
            data = json.loads(prompt.strip())
        except json.JSONDecodeError:
            return prompt
        return _render_answers(data)

    # 检测 <<RESUME_ANSWERS>> 格式（旧格式）
    if RESUME_MARKER in prompt:
        data = parse_resume_answer_payload(prompt)
        if data is None:
            return prompt
        return _render_answers(data)

    return prompt


def _render_answers(data: dict) -> str:
    """将解析后的答案数据渲染为 LLM 可读文本。"""
    answers = data.get("answers", {}) if isinstance(data, dict) else {}
    if not answers or not isinstance(answers, dict):
        return "跳过补充需求，请继续生成。"

    lines = ["需求补充："]
    question_set_id = data.get("questionSetId") or data.get("question_set_id")
    if question_set_id:
        lines.append(f"[questionSetId]: {question_set_id}")
    for key, value in answers.items():
        lines.append(f"[{key}]: {value}")
    lines.append("")
    lines.append("请继续生成。")

    return "\n".join(lines)


def parse_resume_answer_payload(prompt: str) -> dict | None:
    """从 prompt 中提取 resume 答案 JSON payload。不含标记或格式错误时返回 None。"""
    if RESUME_MARKER not in prompt:
        return None

    pattern = re.escape(RESUME_MARKER) + r"(.*?)" + re.escape(RESUME_MARKER)
    match = re.search(pattern, prompt, re.DOTALL)
    if not match:
        return None

    json_str = match.group(1).strip()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("resume 答案 JSON 解析失败, error=%s", e)
        return None

    if not isinstance(data, dict):
        logger.warning("resume 答案数据格式异常, data=%s", data)
        return None
    return data


__all__ = [
    "RESUME_MARKER",
    "PLANNING_RESUME_TYPE",
    "parse_resume_answer_payload",
    "render_resume_answer_text",
]
