import pytest

from app.services.prompt_builder import PromptBuilder


def test_build_vue_app_prompt_contains_user_requirement():
    builder = PromptBuilder()
    result = builder.build_vue_app_prompt("创建一个简洁的个人作品集首页")

    assert "创建一个简洁的个人作品集首页" in result


def test_build_vue_app_prompt_contains_vue3_sfc_requirement():
    builder = PromptBuilder()
    result = builder.build_vue_app_prompt("创建一个首页")

    assert "Vue 3" in result
    assert "单文件组件" in result
    assert ".vue" in result


def test_build_vue_app_prompt_contains_no_markdown_fence_requirement():
    builder = PromptBuilder()
    result = builder.build_vue_app_prompt("创建一个首页")

    assert "markdown" in result.lower() or "代码块" in result
    assert "```" in result or "代码围栏" in result or "code fence" in result.lower()


def test_build_vue_app_prompt_contains_file_target():
    builder = PromptBuilder()
    result = builder.build_vue_app_prompt("创建一个首页")

    assert "src/App.vue" in result


def test_build_vue_app_prompt_rejects_empty_user_prompt():
    builder = PromptBuilder()
    with pytest.raises(ValueError):
        builder.build_vue_app_prompt("")
