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

        assert len(result) > 0
        assert result[0].id == "dashboard"

    def test_select_returns_empty_list_when_no_match(self):
        registry = SkillRegistry()
        registry.register(
            _make_skill("dashboard", "Dashboard", ("dashboard", "后台"), scenario="operations")
        )

        selector = SkillSelector()
        result = selector.select("帮我写一首诗", registry)

        assert result == []

    def test_chinese_trigger_matching(self):
        registry = SkillRegistry()
        registry.register(
            _make_skill("dashboard", "Dashboard", ("dashboard", "后台"), scenario="operations")
        )

        selector = SkillSelector()
        result = selector.select("我要一个后台管理界面", registry)

        assert len(result) > 0
        assert result[0].id == "dashboard"

    def test_highest_score_wins(self):
        registry = SkillRegistry()
        registry.register(_make_skill("a-skill", "A", ("dashboard",), scenario="operations"))
        registry.register(_make_skill("b-skill", "B", ("dashboard", "后台"), scenario="operations"))

        selector = SkillSelector()
        result = selector.select("后台dashboard", registry)

        assert len(result) > 0
        assert result[0].id == "b-skill"

    def test_same_score_alphabetical_tiebreak(self):
        registry = SkillRegistry()
        registry.register(_make_skill("zebra", "Zebra", ("dashboard",), scenario=""))
        registry.register(_make_skill("alpha", "Alpha", ("dashboard",), scenario=""))

        selector = SkillSelector()
        result = selector.select("dashboard", registry)

        assert len(result) > 0
        assert result[0].id == "alpha"

    def test_scenario_bonus(self):
        registry = SkillRegistry()
        registry.register(_make_skill("dash-a", "DashA", ("dashboard",), scenario="operations"))
        registry.register(_make_skill("dash-b", "DashB", ("dashboard",), scenario=""))

        selector = SkillSelector()
        result = selector.select("dashboard operations", registry)

        assert len(result) > 0
        assert result[0].id == "dash-a"

    def test_empty_registry_returns_empty_list(self):
        registry = SkillRegistry()
        selector = SkillSelector()
        result = selector.select("dashboard", registry)

        assert result == []

    def test_select_returns_sorted_list_by_relevance(self):
        registry = SkillRegistry()
        registry.register(
            _make_skill("landing", "Landing", ("landing", "page"), scenario="marketing")
        )
        registry.register(
            _make_skill("dashboard", "Dashboard", ("dashboard", "后台"), scenario="operations")
        )

        selector = SkillSelector()
        result = selector.select("后台 dashboard page", registry)

        assert [skill.id for skill in result] == ["dashboard", "landing"]
