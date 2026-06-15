from pathlib import Path

from app.capabilities.common.capability_selection import CapabilitySelection
from app.capabilities.common.loader_result import SelectedCapabilities
from app.capabilities.skills.prompt_module import SelectedSkillModule
from app.capabilities.skills.types import (
    SkillCraftRequirement,
    SkillDefinition,
    SkillDesignSystemRequirement,
)


def _make_state(skill: SkillDefinition | None):
    selection = CapabilitySelection(skill_ids=(skill.id,) if skill else ())
    selected = SelectedCapabilities(
        selection=selection,
        skills=[skill] if skill else [],
    )
    state = type("State", (), {})()
    state.selected_capabilities = selected
    return state


def test_skill_prompt_rewrites_open_design_artifact_contract():
    skill = SkillDefinition(
        id="dashboard",
        name="dashboard",
        description="Dashboard screen.",
        triggers=("dashboard",),
        mode="prototype",
        platform="desktop",
        scenario="operations",
        preview=None,
        design_system=SkillDesignSystemRequirement(requires=True),
        craft=SkillCraftRequirement(requires=("state-coverage",)),
        body="Emit between <artifact> tags and write one self-contained HTML document.",
        source_path=Path("SKILL.md"),
        output_contract="single_html_file",
    )

    rendered = SelectedSkillModule().render(context=None, state=_make_state(skill))

    assert "Use file tools to write real project files" in rendered
    assert "<artifact>" not in rendered
    assert "self-contained HTML" not in rendered
    assert "### Project Output Contract" in rendered


def test_skill_prompt_appends_output_contract_with_expected_contract():
    skill = SkillDefinition(
        id="web-prototype",
        name="web-prototype",
        description="Web prototype.",
        triggers=("prototype",),
        mode="prototype",
        platform="desktop",
        scenario="design",
        preview=None,
        design_system=SkillDesignSystemRequirement(requires=True),
        craft=SkillCraftRequirement(requires=("typography", "color")),
        body="Build a prototype.",
        source_path=Path("SKILL.md"),
        output_contract="single_html_file",
    )

    rendered = SelectedSkillModule().render(context=None, state=_make_state(skill))

    assert "### Project Output Contract" in rendered
    assert "Expected output contract: single_html_file" in rendered
    assert "write_file" in rendered
    assert "loading, empty, error, and normal states" in rendered


def test_skill_prompt_enabled_only_when_skill_present():
    module = SelectedSkillModule()

    skill = SkillDefinition(
        id="dashboard",
        name="dashboard",
        description="Dashboard screen.",
        triggers=("dashboard",),
        mode="prototype",
        platform="desktop",
        scenario="operations",
        preview=None,
        design_system=SkillDesignSystemRequirement(requires=True),
        craft=SkillCraftRequirement(requires=("state-coverage",)),
        body="Build a dashboard.",
        source_path=Path("SKILL.md"),
    )

    assert module.enabled(context=None, state=_make_state(skill)) is True
    assert module.enabled(context=None, state=_make_state(None)) is False


def test_skill_prompt_returns_empty_when_no_selected_capabilities():
    state = type("State", (), {})()
    state.selected_capabilities = None

    rendered = SelectedSkillModule().render(context=None, state=state)

    assert rendered == ""


def test_skill_prompt_replaces_single_self_contained_html():
    skill = SkillDefinition(
        id="landing-page",
        name="landing-page",
        description="Landing page.",
        triggers=("landing",),
        mode="prototype",
        platform="desktop",
        scenario="marketing",
        preview=None,
        design_system=SkillDesignSystemRequirement(requires=True),
        craft=SkillCraftRequirement(requires=("typography", "color", "anti-ai-slop")),
        body="Produce a single, self-contained HTML landing page between <artifact> tags.",
        source_path=Path("SKILL.md"),
    )

    rendered = SelectedSkillModule().render(context=None, state=_make_state(skill))

    assert "project files" in rendered
    assert "<artifact>" not in rendered
