from pathlib import Path

from app.quality.checks import check_ai_default_indigo, check_vue_state_coverage


def test_check_ai_default_indigo_fails_for_common_ai_purple(tmp_path: Path):
    app_vue = tmp_path / "src" / "App.vue"
    app_vue.parent.mkdir()
    app_vue.write_text(
        "<template><main style='color: #6366f1'>AI</main></template>", encoding="utf-8"
    )

    result = check_ai_default_indigo(tmp_path, ["src/App.vue"])

    assert result.status == "fail"
    assert result.severity == "warning"
    assert "#6366f1" in result.message


def test_check_ai_default_indigo_passes_when_no_default_colors(tmp_path: Path):
    app_vue = tmp_path / "src" / "App.vue"
    app_vue.parent.mkdir()
    app_vue.write_text(
        "<template><main style='color: #c96442'>AI</main></template>", encoding="utf-8"
    )

    result = check_ai_default_indigo(tmp_path, ["src/App.vue"])

    assert result.status == "pass"


def test_check_vue_state_coverage_warns_when_no_empty_error_loading_state(tmp_path: Path):
    app_vue = tmp_path / "src" / "App.vue"
    app_vue.parent.mkdir()
    app_vue.write_text("<template><main>content</main></template>", encoding="utf-8")

    result = check_vue_state_coverage(tmp_path, ["src/App.vue"])

    assert result.status == "warn"
    assert result.severity == "warning"


def test_check_vue_state_coverage_passes_when_loading_state_present(tmp_path: Path):
    app_vue = tmp_path / "src" / "App.vue"
    app_vue.parent.mkdir()
    app_vue.write_text("<template><main v-if='loading'>加载中</main></template>", encoding="utf-8")

    result = check_vue_state_coverage(tmp_path, ["src/App.vue"])

    assert result.status == "pass"
