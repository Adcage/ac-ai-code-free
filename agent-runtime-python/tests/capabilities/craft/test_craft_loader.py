from pathlib import Path

from app.capabilities.common.asset_paths import AssetPathConfig
from app.capabilities.craft.loader import CraftLoader
from app.capabilities.craft.registry import CraftRegistry
from app.capabilities.craft.types import CraftDefinition


ACCESSIBILITY_MD = """\
---
id: accessibility-baseline
name: Accessibility Baseline
description: Baseline accessibility constraints for generated UI.
appliesTo: ["vue_project", "multi-file", "single_file"]
priority: 50
---

# Accessibility Baseline

- Interactive controls must have accessible names.
- Text contrast must be readable.
- Form inputs must have labels or aria-label.
"""

ANTI_SLOP_MD = """\
---
id: anti-slop
name: Anti Slop
description: Prevent low-quality placeholder content.
appliesTo: []
priority: 10
---

# Anti Slop

- No lorem ipsum.
- No Metric A / Card 1.
- No meaningless gradient stacking.
- No bare-bones demo with only title, input, and button.
"""

STATE_COVERAGE_MD = """\
---
id: state-coverage
name: State Coverage
description: Ensure pages cover loading, empty, and error states.
appliesTo: ["vue_project", "multi-file"]
priority: 30
---

# State Coverage

- Pages should include loading, empty, and error states or reasonable static alternatives.
- Data cards must not be all placeholders.
"""


class TestCraftLoader:
    def test_load_craft_from_markdown(self, tmp_path: Path):
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "accessibility-baseline.md").write_text(ACCESSIBILITY_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        craft = registry.get("accessibility-baseline")
        assert isinstance(craft, CraftDefinition)
        assert craft.name == "Accessibility Baseline"
        assert craft.description == "Baseline accessibility constraints for generated UI."
        assert craft.applies_to == ("vue_project", "multi-file", "single_file")
        assert craft.priority == 50
        assert "Interactive controls" in craft.body

    def test_load_multiple_crafts_sorted_by_priority(self, tmp_path: Path):
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "accessibility-baseline.md").write_text(ACCESSIBILITY_MD, encoding="utf-8")
        (craft_dir / "anti-slop.md").write_text(ANTI_SLOP_MD, encoding="utf-8")
        (craft_dir / "state-coverage.md").write_text(STATE_COVERAGE_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        all_crafts = registry.all()
        assert len(all_crafts) == 3

    def test_load_uses_filename_when_name_missing(self, tmp_path: Path):
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "broken.md").write_text("---\n---\nBody only", encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        craft = registry.get("broken")
        assert craft.name == "Broken"
        assert craft.body == "Body only"

    def test_load_craft_without_frontmatter_uses_filename(self, tmp_path: Path):
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "laws-of-ux.md").write_text(
            "# Laws of UX\n\n- Use proximity.", encoding="utf-8"
        )

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        craft = registry.get("laws-of-ux")
        assert craft.name == "Laws Of Ux"
        assert craft.description == ""
        assert craft.priority == 100
        assert craft.applies_to == ()
        assert "Use proximity" in craft.body

    def test_load_no_craft_dir(self, tmp_path: Path):
        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_craft_without_applies_to(self, tmp_path: Path):
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "anti-slop.md").write_text(ANTI_SLOP_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        craft = registry.get("anti-slop")
        assert craft.applies_to == ()

    def test_load_craft_default_priority(self, tmp_path: Path):
        md = """\
---
id: no-priority
name: No Priority
description: Craft without priority field.
---

# No Priority

Some rules.
"""
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "no-priority.md").write_text(md, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        craft = registry.get("no-priority")
        assert craft.priority == 100

    def test_duplicate_id_across_roots_skips_lower_priority(self, tmp_path: Path):
        root_project = tmp_path / "project"
        root_bundled = tmp_path / "bundled"
        for root in (root_project, root_bundled):
            craft_dir = root / "craft"
            craft_dir.mkdir(parents=True)
            (craft_dir / "anti-slop.md").write_text(ANTI_SLOP_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=root_bundled, project_root=root_project)
        loader = CraftLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 1

    def test_higher_priority_root_overrides(self, tmp_path: Path):
        root_project = tmp_path / "project"
        root_bundled = tmp_path / "bundled"

        for root in (root_project, root_bundled):
            craft_dir = root / "craft"
            craft_dir.mkdir(parents=True)

        project_md = """\
---
id: anti-slop
name: Anti Slop Custom
description: Custom anti slop.
priority: 5
---

# Custom Anti Slop
"""
        (root_project / "craft" / "anti-slop.md").write_text(project_md, encoding="utf-8")
        (root_bundled / "craft" / "anti-slop.md").write_text(ANTI_SLOP_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=root_bundled, project_root=root_project)
        loader = CraftLoader()
        registry = loader.load(config)

        craft = registry.get("anti-slop")
        assert craft.name == "Anti Slop Custom"

    def test_load_skips_non_markdown_files(self, tmp_path: Path):
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "notes.txt").write_text("not a craft", encoding="utf-8")
        (craft_dir / "anti-slop.md").write_text(ANTI_SLOP_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = CraftLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 1


class TestCraftRegistry:
    def test_all_returns_registered_crafts(self):
        registry = CraftRegistry()
        craft = CraftDefinition(
            id="test",
            name="Test",
            description="Test craft",
            applies_to=(),
            priority=50,
            body="Body",
            source_path=Path("/test"),
        )
        registry.register(craft)
        result = registry.all()
        assert len(result) == 1
        assert result[0].id == "test"

    def test_all_returns_empty_tuple_when_no_crafts(self):
        registry = CraftRegistry()
        assert registry.all() == ()
