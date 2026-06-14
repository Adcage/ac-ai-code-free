from pathlib import Path

from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.skills.selector import SkillSelector
from app.capabilities.skills.types import (
    SkillCraftRequirement,
    SkillDefinition,
    SkillDesignSystemRequirement,
)


def _make_skill(
    id: str,
    name: str,
    triggers: tuple[str, ...],
    scenario: str = "",
) -> SkillDefinition:
    return SkillDefinition(
        id=id,
        name=name,
        description=f"{name} skill",
        triggers=triggers,
        mode="prototype",
        platform="desktop",
        scenario=scenario,
        preview=None,
        design_system=SkillDesignSystemRequirement(),
        craft=SkillCraftRequirement(),
        body=f"# {name}",
        source_path=Path(f"/skills/{id}/SKILL.md"),
    )


class TestSkillSelector:
    def test_select_dashboard_by_chinese_trigger(self):
        registry = SkillRegistry()
        registry.register(
            _make_skill(
                "dashboard", "Dashboard", ("dashboard", "后台", "看板"), scenario="operations"
            )
        )
        registry.register(
            _make_skill("landing", "Landing", ("landing", "首页"), scenario="marketing")
        )

        selector = SkillSelector()
        result = selector.select("帮我生成一个后台数据看板", registry)

        assert result is not None
        assert result.id == "dashboard"

    def test_select_returns_none_when_no_match(self):
        registry = SkillRegistry()
        registry.register(
            _make_skill("dashboard", "Dashboard", ("dashboard", "后台"), scenario="operations")
        )

        selector = SkillSelector()
        result = selector.select("帮我写一首诗", registry)

        assert result is None

    def test_chinese_trigger_matching(self):
        registry = SkillRegistry()
        registry.register(
            _make_skill("dashboard", "Dashboard", ("dashboard", "后台"), scenario="operations")
        )

        selector = SkillSelector()
        result = selector.select("我要一个后台管理界面", registry)

        assert result is not None
        assert result.id == "dashboard"

    def test_highest_score_wins(self):
        registry = SkillRegistry()
        registry.register(_make_skill("a-skill", "A", ("dashboard",), scenario="operations"))
        registry.register(_make_skill("b-skill", "B", ("dashboard", "后台"), scenario="operations"))

        selector = SkillSelector()
        result = selector.select("后台dashboard", registry)

        assert result is not None
        assert result.id == "b-skill"

    def test_same_score_alphabetical_tiebreak(self):
        registry = SkillRegistry()
        registry.register(_make_skill("zebra", "Zebra", ("dashboard",), scenario=""))
        registry.register(_make_skill("alpha", "Alpha", ("dashboard",), scenario=""))

        selector = SkillSelector()
        result = selector.select("dashboard", registry)

        assert result is not None
        assert result.id == "alpha"

    def test_scenario_bonus(self):
        registry = SkillRegistry()
        registry.register(_make_skill("dash-a", "DashA", ("dashboard",), scenario="operations"))
        registry.register(_make_skill("dash-b", "DashB", ("dashboard",), scenario=""))

        selector = SkillSelector()
        result = selector.select("dashboard operations", registry)

        assert result is not None
        assert result.id == "dash-a"

    def test_empty_registry_returns_none(self):
        registry = SkillRegistry()
        selector = SkillSelector()
        result = selector.select("dashboard", registry)

        assert result is None
