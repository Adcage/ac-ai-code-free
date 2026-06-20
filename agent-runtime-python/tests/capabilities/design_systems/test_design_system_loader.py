import json
from pathlib import Path

from app.capabilities.common.asset_paths import AssetPathConfig
from app.capabilities.design_systems.loader import DesignSystemLoader
from app.capabilities.design_systems.registry import DesignSystemRegistry
from app.capabilities.design_systems.types import DesignSystemDefinition, DesignSystemFiles

DEFAULT_MANIFEST = {
    "schemaVersion": "ac-design-system/v1",
    "id": "default",
    "name": "Default",
    "category": "Product UI",
    "description": "Default product UI design system.",
    "files": {
        "design": "DESIGN.md",
        "tokens": "tokens.css",
    },
    "importMode": "normalized",
    "craft": {
        "suggested": ["accessibility-baseline"],
    },
}

DEFAULT_DESIGN_MD = "# Default Design System\n\nUse primary color for main actions."

DEFAULT_TOKENS_CSS = ":root {\n  --color-primary: #1677ff;\n  --color-text: #111827;\n}\n"


def _create_default_ds(base: Path) -> None:
    ds_dir = base / "design-systems" / "default"
    ds_dir.mkdir(parents=True)
    (ds_dir / "manifest.json").write_text(json.dumps(DEFAULT_MANIFEST), encoding="utf-8")
    (ds_dir / "DESIGN.md").write_text(DEFAULT_DESIGN_MD, encoding="utf-8")
    (ds_dir / "tokens.css").write_text(DEFAULT_TOKENS_CSS, encoding="utf-8")


class TestDesignSystemLoader:
    def test_load_default_design_system(self, tmp_path: Path):
        _create_default_ds(tmp_path)

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        ds = registry.get("default")
        assert isinstance(ds, DesignSystemDefinition)
        assert ds.id == "default"
        assert ds.name == "Default"
        assert ds.category == "Product UI"
        assert ds.description == "Default product UI design system."
        assert ds.import_mode == "normalized"
        assert ds.files.design.name == "DESIGN.md"
        assert ds.files.tokens is not None
        assert ds.files.tokens.name == "tokens.css"
        assert ds.suggested_craft == ("accessibility-baseline",)

    def test_load_skips_missing_design_file(self, tmp_path: Path):
        ds_dir = tmp_path / "design-systems" / "broken"
        ds_dir.mkdir(parents=True)
        manifest = {
            "schemaVersion": "ac-design-system/v1",
            "id": "broken",
            "name": "Broken",
            "category": "Test",
            "description": "Missing design file",
            "files": {"design": "DESIGN.md"},
            "importMode": "normalized",
        }
        (ds_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_skips_invalid_manifest(self, tmp_path: Path):
        ds_dir = tmp_path / "design-systems" / "bad-json"
        ds_dir.mkdir(parents=True)
        (ds_dir / "manifest.json").write_text("not valid json{{{", encoding="utf-8")
        (ds_dir / "DESIGN.md").write_text("# Test", encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_skips_manifest_missing_id(self, tmp_path: Path):
        ds_dir = tmp_path / "design-systems" / "no-id"
        ds_dir.mkdir(parents=True)
        manifest = {
            "schemaVersion": "ac-design-system/v1",
            "name": "No ID",
            "files": {"design": "DESIGN.md"},
        }
        (ds_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (ds_dir / "DESIGN.md").write_text("# Test", encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_no_design_systems_dir(self, tmp_path: Path):
        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_optional_files_missing_gracefully(self, tmp_path: Path):
        ds_dir = tmp_path / "design-systems" / "minimal"
        ds_dir.mkdir(parents=True)
        manifest = {
            "schemaVersion": "ac-design-system/v1",
            "id": "minimal",
            "name": "Minimal",
            "category": "Test",
            "description": "Only required files",
            "files": {"design": "DESIGN.md"},
            "importMode": "normalized",
        }
        (ds_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (ds_dir / "DESIGN.md").write_text("# Minimal Design System", encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        ds = registry.get("minimal")
        assert ds.id == "minimal"
        assert ds.files.tokens is None
        assert ds.files.design_tokens is None
        assert ds.files.components_manifest is None
        assert ds.files.components is None
        assert ds.files.usage is None

    def test_load_with_all_optional_files(self, tmp_path: Path):
        ds_dir = tmp_path / "design-systems" / "full"
        ds_dir.mkdir(parents=True)
        manifest = {
            "schemaVersion": "ac-design-system/v1",
            "id": "full",
            "name": "Full",
            "category": "Test",
            "description": "All files",
            "files": {
                "design": "DESIGN.md",
                "tokens": "tokens.css",
                "design_tokens": "design-tokens.json",
                "components_manifest": "components.manifest.json",
                "components": "components.html",
                "usage": "USAGE.md",
            },
            "importMode": "normalized",
            "craft": {"suggested": ["accessibility-baseline", "state-coverage"]},
        }
        (ds_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (ds_dir / "DESIGN.md").write_text("# Full", encoding="utf-8")
        (ds_dir / "tokens.css").write_text(":root { --color-primary: #000; }", encoding="utf-8")
        (ds_dir / "design-tokens.json").write_text("{}", encoding="utf-8")
        (ds_dir / "components.manifest.json").write_text(
            '{"components": [{"name": "Button", "description": "A button"}]}', encoding="utf-8"
        )
        (ds_dir / "components.html").write_text("<div>Button</div>", encoding="utf-8")
        (ds_dir / "USAGE.md").write_text("# Usage\n- Rule 1", encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        ds = registry.get("full")
        assert ds.files.tokens is not None
        assert ds.files.design_tokens is not None
        assert ds.files.components_manifest is not None
        assert ds.files.components is not None
        assert ds.files.usage is not None
        assert ds.suggested_craft == ("accessibility-baseline", "state-coverage")

    def test_duplicate_id_across_roots_skips_lower_priority(self, tmp_path: Path):
        root_project = tmp_path / "project"
        root_bundled = tmp_path / "bundled"
        for root in (root_project, root_bundled):
            _create_default_ds(root)

        config = AssetPathConfig(bundled_root=root_bundled, project_root=root_project)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 1

    def test_higher_priority_root_overrides(self, tmp_path: Path):
        root_project = tmp_path / "project"
        root_bundled = tmp_path / "bundled"

        _create_default_ds(root_project)
        _create_default_ds(root_bundled)

        project_manifest = {
            "schemaVersion": "ac-design-system/v1",
            "id": "default",
            "name": "Custom Default",
            "category": "Custom",
            "description": "Custom override",
            "files": {"design": "DESIGN.md"},
            "importMode": "normalized",
        }
        ds_dir = root_project / "design-systems" / "default"
        (ds_dir / "manifest.json").write_text(json.dumps(project_manifest), encoding="utf-8")
        (ds_dir / "DESIGN.md").write_text("# Custom", encoding="utf-8")

        config = AssetPathConfig(bundled_root=root_bundled, project_root=root_project)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        ds = registry.get("default")
        assert ds.name == "Custom Default"

    def test_supports_open_design_camel_case_manifest_keys(self, tmp_path: Path):
        ds_dir = tmp_path / "design-systems" / "ant"
        ds_dir.mkdir(parents=True)
        (ds_dir / "DESIGN.md").write_text("# Ant Design", encoding="utf-8")
        (ds_dir / "tokens.css").write_text(":root { --color-primary: #1677ff; }", encoding="utf-8")
        (ds_dir / "components.manifest.json").write_text('{"components": []}', encoding="utf-8")
        (ds_dir / "USAGE.md").write_text("# Usage\n- Use primary color.", encoding="utf-8")
        manifest = {
            "schemaVersion": "od-design-system-project/v1",
            "id": "ant",
            "name": "Ant",
            "category": "Professional & Corporate",
            "files": {
                "design": "DESIGN.md",
                "tokens": "tokens.css",
            },
            "componentsManifest": "components.manifest.json",
            "usage": "USAGE.md",
            "importMode": "normalized",
            "craft": {"suggested": ["color", "accessibility-baseline"]},
        }
        (ds_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = DesignSystemLoader()
        registry = loader.load(config)

        ds = registry.get("ant")
        assert ds is not None
        assert ds.files.components_manifest is not None
        assert ds.files.components_manifest.name == "components.manifest.json"
        assert ds.files.usage is not None
        assert ds.files.usage.name == "USAGE.md"
        assert ds.suggested_craft == ("color", "accessibility-baseline")


class TestDesignSystemRegistry:
    def test_all_returns_registered_design_systems(self, tmp_path: Path):
        registry = DesignSystemRegistry()
        ds = DesignSystemDefinition(
            id="test",
            name="Test",
            category="Test",
            description="Test DS",
            import_mode="normalized",
            files=DesignSystemFiles(design=tmp_path / "DESIGN.md"),
            source_path=tmp_path,
        )
        registry.register(ds)
        result = registry.all()
        assert len(result) == 1
        assert result[0].id == "test"

    def test_all_returns_empty_tuple_when_no_design_systems(self):
        registry = DesignSystemRegistry()
        assert registry.all() == ()
