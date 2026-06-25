"""resume_answers — 恢复运行时的用户答案渲染工具。

在 Agent 恢复运行（resume）时，之前 ask_user 收集到的用户答案编码在
prompt 文本中，格式为：

    {PLANNING_RESUME_PREFIX}{JSON}{PLANNING_RESUME_SUFFIX}

render_resume_answer_text 将其解析并格式化为 LLM 易于理解的文本。
"""

import json
import logging
import re

logger = logging.getLogger("app.agent_loop.resume_answers")

PLANNING_RESUME_PREFIX = "<<RESUME_ANSWERS>>"
PLANNING_RESUME_SUFFIX = "<<RESUME_ANSWERS>>"


def render_resume_answer_text(prompt: str) -> str:
    """将包含编码答案的 prompt 渲染为纯文本。

    输入示例:
        <<RESUME_ANSWERS>>{"questionSetId":"qs1","answers":{"q_device":"desktop"}}<<RESUME_ANSWERS>>

    输出示例:
        需求补充：
        [q_device]: desktop

        请继续生成。
    """
    if PLANNING_RESUME_PREFIX not in prompt or PLANNING_RESUME_SUFFIX not in prompt:
        logger.warning("prompt 中未找到 resume 答案标记，返回原文本")
        return prompt

    data = parse_resume_answer_payload(prompt)
    if data is None:
        return prompt

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
    """解析结构化 resume 答案 payload；不含标记或格式错误时返回 None。"""
    if PLANNING_RESUME_PREFIX not in prompt or PLANNING_RESUME_SUFFIX not in prompt:
        logger.warning("prompt 中未找到 resume 答案标记，返回原文本")
        return None

    pattern = re.escape(PLANNING_RESUME_PREFIX) + r"(.*?)" + re.escape(PLANNING_RESUME_SUFFIX)
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
    "PLANNING_RESUME_PREFIX",
    "PLANNING_RESUME_SUFFIX",
    "parse_resume_answer_payload",
    "render_resume_answer_text",
]
