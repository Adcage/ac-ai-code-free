from pathlib import Path

from app.capabilities.common.asset_paths import AssetPathConfig
from app.capabilities.skills.loader import SkillLoader
from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.skills.types import SkillDefinition


DASHBOARD_SKILL_MD = """\
---
name: dashboard
description: Dashboard screen.
triggers:
  - dashboard
  - 后台
  - 看板
od:
  mode: prototype
  platform: desktop
  scenario: operations
  preview:
    type: html
    entry: index.html
  design_system:
    requires: true
    sections: [color, typography, layout]
  craft:
    requires: [state-coverage, accessibility-baseline]
ac:
  when_to_use: "Use when generating a dashboard."
  target_code_gen_types: ["single_file", "multi_file", "vue_project"]
  related_templates: ["dashboard"]
  recommended_seeds: ["vue-dashboard"]
  output_contract: "single_html_file"
---

# Dashboard Skill

Build a dashboard with real data and complete functionality.
"""


class TestSkillLoader:
    def test_load_dashboard_skill(self, tmp_path: Path):
        skill_dir = tmp_path / "skills" / "dashboard"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(DASHBOARD_SKILL_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = SkillLoader()
        registry = loader.load(config)

        skill = registry.get("dashboard")
        assert isinstance(skill, SkillDefinition)
        assert skill.name == "dashboard"
        assert skill.description == "Dashboard screen."
        assert "后台" in skill.triggers
        assert "dashboard" in skill.triggers
        assert skill.mode == "prototype"
        assert skill.platform == "desktop"
        assert skill.scenario == "operations"
        assert skill.preview is not None
        assert skill.preview.type == "html"
        assert skill.preview.entry == "index.html"
        assert skill.design_system.requires is True
        assert "color" in skill.design_system.sections
        assert "state-coverage" in skill.craft.requires
        assert "accessibility-baseline" in skill.craft.requires
        assert "Build a dashboard" in skill.body

    def test_load_skill_ac_extension_fields(self, tmp_path: Path):
        skill_dir = tmp_path / "skills" / "dashboard"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(DASHBOARD_SKILL_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = SkillLoader()
        registry = loader.load(config)

        skill = registry.get("dashboard")
        assert isinstance(skill, SkillDefinition)
        assert skill.when_to_use == "Use when generating a dashboard."
        assert skill.target_code_gen_types == ("single_file", "multi_file", "vue_project")
        assert skill.related_templates == ("dashboard",)
        assert skill.recommended_seeds == ("vue-dashboard",)
        assert skill.output_contract == "single_html_file"

    def test_load_skips_invalid_skill(self, tmp_path: Path):
        skill_dir = tmp_path / "skills" / "broken"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: broken\n---\nBody", encoding="utf-8")

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = SkillLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_skips_directory_without_skill_md(self, tmp_path: Path):
        skill_dir = tmp_path / "skills" / "empty"
        skill_dir.mkdir(parents=True)

        config = AssetPathConfig(bundled_root=tmp_path)
        loader = SkillLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_load_no_skills_dir(self, tmp_path: Path):
        config = AssetPathConfig(bundled_root=tmp_path)
        loader = SkillLoader()
        registry = loader.load(config)

        assert len(registry.all()) == 0

    def test_duplicate_id_across_roots_skips_lower_priority(self, tmp_path: Path):
        root_project = tmp_path / "project"
        root_bundled = tmp_path / "bundled"
        for root in (root_project, root_bundled):
            skill_dir = root / "skills" / "dashboard"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(DASHBOARD_SKILL_MD, encoding="utf-8")

        config = AssetPathConfig(bundled_root=root_bundled, project_root=root_project)
        loader = SkillLoader()
        registry = loader.load(config)

        skill = registry.get("dashboard")
        assert skill.name == "dashboard"
        assert len(registry.all()) == 1

    def test_higher_priority_root_overrides(self, tmp_path: Path):
        root_project = tmp_path / "project"
        root_bundled = tmp_path / "bundled"

        for root in (root_project, root_bundled):
            skill_dir = root / "skills" / "dashboard"
            skill_dir.mkdir(parents=True)

        project_md = """\
---
name: dashboard-custom
description: Custom dashboard.
triggers:
  - dashboard
od:
  mode: prototype
  platform: desktop
  scenario: operations
---

# Custom Dashboard
"""
        (root_project / "skills" / "dashboard" / "SKILL.md").write_text(
            project_md, encoding="utf-8"
        )
        (root_bundled / "skills" / "dashboard" / "SKILL.md").write_text(
            DASHBOARD_SKILL_MD, encoding="utf-8"
        )

        config = AssetPathConfig(bundled_root=root_bundled, project_root=root_project)
        loader = SkillLoader()
        registry = loader.load(config)

        skill = registry.get("dashboard")
        assert skill.name == "dashboard-custom"


class TestSkillRegistry:
    def test_all_returns_registered_skills(self):
        registry = SkillRegistry()
        skill = SkillDefinition(
            id="test",
            name="Test",
            description="Test skill",
            triggers=("test",),
            mode="prototype",
            platform="desktop",
            scenario="test",
            preview=None,
            design_system=SkillDefinition.__dataclass_fields__["design_system"].default,
            craft=SkillDefinition.__dataclass_fields__["craft"].default,
            body="Body",
            source_path=Path("/test"),
        )
        registry.register(skill)
        result = registry.all()
        assert len(result) == 1
        assert result[0].id == "test"

    def test_all_returns_empty_tuple_when_no_skills(self):
        registry = SkillRegistry()
        assert registry.all() == ()
