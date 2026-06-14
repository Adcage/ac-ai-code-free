from pathlib import Path

from app.capabilities.common.loader_result import SelectedCapabilities
from app.capabilities.templates.prompt_module import TemplateReferenceModule
from app.capabilities.templates.types import TemplateDefinition


def _make_template(
    id: str = "dashboard-analytics",
    name: str = "Analytics Dashboard",
    max_prompt_files: int = 3,
    files: tuple[Path, ...] | None = None,
    source_path: Path | None = None,
) -> TemplateDefinition:
    return TemplateDefinition(
        id=id,
        name=name,
        description="Dashboard layout",
        code_gen_type="vue_project",
        triggers=("dashboard",),
        entry="files/src/App.vue",
        max_prompt_files=max_prompt_files,
        files=files or (Path("files/src/App.vue"),),
        source_path=source_path or Path("/test/template.json"),
    )


class TestTemplateReferenceModule:
    def test_disabled_when_no_template(self) -> None:
        module = TemplateReferenceModule()
        state = type("State", (), {"selected_capabilities": SelectedCapabilities()})()
        context = object()

        assert module.enabled(context, state) is False

    def test_enabled_when_template_selected(self) -> None:
        module = TemplateReferenceModule()
        caps = SelectedCapabilities(template=_make_template())
        state = type("State", (), {"selected_capabilities": caps})()
        context = object()

        assert module.enabled(context, state) is True

    def test_render_includes_template_name(self, tmp_path: Path) -> None:
        template = _make_template_with_files(tmp_path)
        module = TemplateReferenceModule()
        caps = SelectedCapabilities(template=template)
        state = type("State", (), {"selected_capabilities": caps})()
        context = object()

        result = module.render(context, state)
        assert "Analytics Dashboard" in result
        assert "structure reference" in result.lower()

    def test_render_includes_file_content(self, tmp_path: Path) -> None:
        template = _make_template_with_files(tmp_path)
        module = TemplateReferenceModule()
        caps = SelectedCapabilities(template=template)
        state = type("State", (), {"selected_capabilities": caps})()
        context = object()

        result = module.render(context, state)
        assert "Dashboard Content" in result

    def test_render_truncates_long_file(self, tmp_path: Path) -> None:
        template = _make_template_with_files(tmp_path, content="x" * 5000)
        module = TemplateReferenceModule(file_max_chars=100)
        caps = SelectedCapabilities(template=template)
        state = type("State", (), {"selected_capabilities": caps})()
        context = object()

        result = module.render(context, state)
        assert "[truncated]" in result

    def test_render_respects_max_prompt_files(self, tmp_path: Path) -> None:
        template_dir = tmp_path / "dashboard-analytics"
        template_dir.mkdir()
        files_dir = template_dir / "files" / "src"
        files_dir.mkdir(parents=True)

        (files_dir / "App.vue").write_text("<template>A</template>", encoding="utf-8")
        (files_dir / "main.ts").write_text("import A", encoding="utf-8")

        source_path = template_dir / "template.json"
        template = TemplateDefinition(
            id="dashboard-analytics",
            name="Analytics Dashboard",
            description="Test",
            code_gen_type="vue_project",
            triggers=("dashboard",),
            entry="files/src/App.vue",
            max_prompt_files=1,
            files=(Path("files/src/App.vue"), Path("files/src/main.ts")),
            source_path=source_path,
        )

        module = TemplateReferenceModule()
        caps = SelectedCapabilities(template=template)
        state = type("State", (), {"selected_capabilities": caps})()
        context = object()

        result = module.render(context, state)
        assert "App.vue" in result
        assert "main.ts" not in result

    def test_render_returns_empty_when_no_caps(self) -> None:
        module = TemplateReferenceModule()
        state = type("State", (), {"selected_capabilities": None})()
        context = object()

        result = module.render(context, state)
        assert result == ""


def _make_template_with_files(
    tmp_path: Path,
    content: str = "<template>Dashboard Content</template>",
) -> TemplateDefinition:
    template_dir = tmp_path / "dashboard-analytics"
    template_dir.mkdir(exist_ok=True)
    files_dir = template_dir / "files" / "src"
    files_dir.mkdir(parents=True, exist_ok=True)

    (files_dir / "App.vue").write_text(content, encoding="utf-8")

    source_path = template_dir / "template.json"
    return TemplateDefinition(
        id="dashboard-analytics",
        name="Analytics Dashboard",
        description="Dashboard layout",
        code_gen_type="vue_project",
        triggers=("dashboard",),
        entry="files/src/App.vue",
        max_prompt_files=3,
        files=(Path("files/src/App.vue"),),
        source_path=source_path,
    )
