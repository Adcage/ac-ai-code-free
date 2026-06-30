"""vNext resume_answers 单元测试。"""

import pytest
from app.agent_loop_vnext.shared.resume_answers import (
    RESUME_MARKER,
    parse_resume_answer_payload,
    render_resume_answer_text,
)


class TestRenderResumeAnswerText:
    def test_renders_single_answer(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs1","answers":{{"q_device":"desktop"}}}}{RESUME_MARKER}'
        result = render_resume_answer_text(prompt)
        assert "[q_device]: desktop" in result
        assert "请继续生成。" in result

    def test_renders_multiple_answers(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs2","answers":{{"q_theme":"dark","q_layout":"sidebar"}}}}{RESUME_MARKER}'
        result = render_resume_answer_text(prompt)
        assert "[q_theme]: dark" in result
        assert "[q_layout]: sidebar" in result

    def test_no_marker_returns_original(self):
        prompt = "这是一条普通消息"
        result = render_resume_answer_text(prompt)
        assert result == prompt

    def test_empty_answers_renders_skip(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs3","answers":{{}}}}{RESUME_MARKER}'
        result = render_resume_answer_text(prompt)
        assert "跳过补充需求" in result

    def test_invalid_json_returns_original(self):
        prompt = f"{RESUME_MARKER}not-valid-json{RESUME_MARKER}"
        result = render_resume_answer_text(prompt)
        assert result == prompt

    def test_renders_json_format(self):
        """JSON 格式：{"type":"planning_resume","answers":{...}}"""
        prompt = '{"type":"planning_resume","questionSetId":"qs4","answers":{"q_theme":"dark"}}'
        result = render_resume_answer_text(prompt)
        assert "[q_theme]: dark" in result
        assert "请继续生成。" in result

    def test_json_format_multiple_answers(self):
        prompt = '{"type":"planning_resume","answers":{"q1":"a1","q2":"a2"}}'
        result = render_resume_answer_text(prompt)
        assert "[q1]: a1" in result
        assert "[q2]: a2" in result

    def test_json_format_empty_answers(self):
        prompt = '{"type":"planning_resume","answers":{}}'
        result = render_resume_answer_text(prompt)
        assert "跳过补充需求" in result

    def test_plain_json_not_confused(self):
        """普通 JSON（不是 planning_resume）应该原样返回。"""
        prompt = '{"key": "value"}'
        result = render_resume_answer_text(prompt)
        assert result == prompt


class TestParseResumeAnswerPayload:
    def test_parses_valid_payload(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs1","answers":{{"q1":"a1"}}}}{RESUME_MARKER}'
        result = parse_resume_answer_payload(prompt)
        assert result is not None
        assert result["questionSetId"] == "qs1"
        assert result["answers"]["q1"] == "a1"

    def test_no_marker_returns_none(self):
        result = parse_resume_answer_payload("no marker here")
        assert result is None

    def test_invalid_json_returns_none(self):
        prompt = f"{RESUME_MARKER}bad-json{RESUME_MARKER}"
        result = parse_resume_answer_payload(prompt)
        assert result is None
