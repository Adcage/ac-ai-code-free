from app.capabilities.common.capability_selection import CapabilitySelection
from app.capabilities.common.loader_result import SelectedCapabilities


def test_capability_selection_defaults_to_selector_source():
    selection = CapabilitySelection(skill_ids=("dashboard",), seed_id="vue-dashboard")

    assert selection.selection_source == "selector"
    assert selection.skill_ids == ("dashboard",)
    assert selection.seed_id == "vue-dashboard"
    assert selection.template_ids == ()
    assert selection.craft_ids == ()


def test_selected_capabilities_keeps_legacy_skill_template_properties():
    selection = CapabilitySelection(skill_ids=("dashboard",), template_ids=("dashboard-analytics",))
    selected = SelectedCapabilities(
        selection=selection,
        skills=["skill-object"],
        templates=["template-object"],
        craft=["craft-object"],
    )

    assert selected.skill == "skill-object"
    assert selected.template == "template-object"
    assert selected.skills == ["skill-object"]
    assert selected.templates == ["template-object"]


def test_selected_capabilities_skill_property_returns_none_when_empty():
    selection = CapabilitySelection()
    selected = SelectedCapabilities(selection=selection)

    assert selected.skill is None
    assert selected.template is None
