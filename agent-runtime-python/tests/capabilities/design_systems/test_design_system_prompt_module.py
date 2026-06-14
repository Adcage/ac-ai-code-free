from dataclasses import dataclass
from pathlib import Path

from app.capabilities.design_systems.prompt_module import (
    DesignSystemModule,
    DesignSystemModuleConfig,
)
from app.capabilities.design_systems.types import DesignSystemDefinition, DesignSystemFiles


def _make_ds_with_files(
    tmp_path: Path,
    design_content: str = "# Design Rules\n\nUse primary color for buttons.",
    tokens_content: str | None = None,
    components_manifest_content: str | None = None,
    usage_content: str | None = None,
) -> DesignSystemDefinition:
    ds_dir = tmp_path / "ds"
    ds_dir.mkdir(parents=True, exist_ok=True)

    design_path = ds_dir / "DESIGN.md"
    design_path.write_text(design_content, encoding="utf-8")

    tokens_path = None
    if tokens_content is not None:
        tokens_path = ds_dir / "tokens.css"
        tokens_path.write_text(tokens_content, encoding="utf-8")

    components_manifest_path = None
    if components_manifest_content is not None:
        components_manifest_path = ds_dir / "components.manifest.json"
        components_manifest_path.write_text(components_manifest_content, encoding="utf-8")

    usage_path = None
    if usage_content is not None:
        usage_path = ds_dir / "USAGE.md"
        usage_path.write_text(usage_content, encoding="utf-8")

    return DesignSystemDefinition(
        id="test",
        name="Test DS",
        category="Test",
        description="Test",
        import_mode="normalized",
        files=DesignSystemFiles(
            design=design_path,
            tokens=tokens_path,
            components_manifest=components_manifest_path,
            usage=usage_path,
        ),
        source_path=ds_dir,
    )


@dataclass
class FakeSelectedCapabilities:
    design_system: DesignSystemDefinition | None = None


@dataclass
class FakeState:
    selected_capabilities: FakeSelectedCapabilities | None = None


class TestDesignSystemModuleEnabled:
    def test_disabled_when_no_selected_capabilities(self):
        module = DesignSystemModule()
        assert module.enabled(None, FakeState()) is False

    def test_disabled_when_no_design_system(self):
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=None)
        assert module.enabled(None, FakeState(selected_capabilities=caps)) is False

    def test_enabled_when_design_system_selected(self, tmp_path: Path):
        ds = _make_ds_with_files(tmp_path)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        assert module.enabled(None, FakeState(selected_capabilities=caps)) is True


class TestDesignSystemModuleRender:
    def test_render_includes_design_system_name(self, tmp_path: Path):
        ds = _make_ds_with_files(tmp_path)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "## Active Design System: Test DS" in result

    def test_render_includes_design_content(self, tmp_path: Path):
        ds = _make_ds_with_files(tmp_path, design_content="# Design Rules\n\nUse primary color.")
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "### Design Rules" in result
        assert "Use primary color" in result

    def test_render_includes_token_summary(self, tmp_path: Path):
        tokens = ":root {\n  --color-primary: #1677ff;\n  --color-text: #111827;\n}\n"
        ds = _make_ds_with_files(tmp_path, tokens_content=tokens)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "### Token Summary" in result
        assert "--color-primary" in result
        assert "--color-text" in result

    def test_render_includes_component_guidance(self, tmp_path: Path):
        manifest = '{"components": [{"name": "Button", "description": "A button component"}, {"name": "Card", "description": "A card container"}]}'
        ds = _make_ds_with_files(tmp_path, components_manifest_content=manifest)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "### Component Guidance" in result
        assert "Button" in result
        assert "Card" in result

    def test_render_includes_usage_key_rules(self, tmp_path: Path):
        usage = "# Usage\n\n- Always use design tokens\n- Do not hardcode colors"
        ds = _make_ds_with_files(tmp_path, usage_content=usage)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "### Usage Key Rules" in result
        assert "Do not hardcode colors" in result

    def test_render_truncates_long_design_content(self, tmp_path: Path):
        long_content = "x" * 10000
        ds = _make_ds_with_files(tmp_path, design_content=long_content)
        config = DesignSystemModuleConfig(design_max_chars=500)
        module = DesignSystemModule(config=config)
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "... (truncated)" in result
        assert len(result) < 10000

    def test_render_truncates_token_summary_lines(self, tmp_path: Path):
        lines = [f"  --var-{i}: #000;" for i in range(200)]
        tokens = ":root {\n" + "\n".join(lines) + "\n}\n"
        ds = _make_ds_with_files(tmp_path, tokens_content=tokens)
        config = DesignSystemModuleConfig(token_summary_max_lines=50)
        module = DesignSystemModule(config=config)
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "... (more tokens omitted)" in result

    def test_render_truncates_component_entries(self, tmp_path: Path):
        components = [{"name": f"Comp{i}", "description": f"Component {i}"} for i in range(100)]
        manifest = '{"components": ' + str(components).replace("'", '"') + "}"
        ds = _make_ds_with_files(tmp_path, components_manifest_content=manifest)
        config = DesignSystemModuleConfig(components_max_entries=10)
        module = DesignSystemModule(config=config)
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "Comp9" in result
        assert "Comp10" not in result

    def test_render_returns_empty_when_no_design_system(self):
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=None)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert result == ""

    def test_render_without_optional_files(self, tmp_path: Path):
        ds = _make_ds_with_files(tmp_path)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "### Design Rules" in result
        assert "### Token Summary" not in result
        assert "### Component Guidance" not in result
        assert "### Usage Key Rules" not in result

    def test_render_overrides_conflict_statement(self, tmp_path: Path):
        ds = _make_ds_with_files(tmp_path)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "overrides generic visual preferences" in result

    def test_render_token_strips_semicolons(self, tmp_path: Path):
        tokens = ":root {\n  --color-primary: #1677ff;\n  --space-md: 16px;\n}\n"
        ds = _make_ds_with_files(tmp_path, tokens_content=tokens)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        token_section_start = result.index("### Token Summary")
        token_section = result[token_section_start:]
        assert "- --color-primary: #1677ff" in token_section
        assert "; " not in token_section.split("\n")[2]

    def test_render_component_without_description(self, tmp_path: Path):
        manifest = '{"components": [{"name": "Button"}]}'
        ds = _make_ds_with_files(tmp_path, components_manifest_content=manifest)
        module = DesignSystemModule()
        caps = FakeSelectedCapabilities(design_system=ds)
        result = module.render(None, FakeState(selected_capabilities=caps))

        assert "- Button" in result
