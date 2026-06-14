from pathlib import Path

from app.capabilities.templates.selector import TemplateSelector
from app.capabilities.templates.types import TemplateDefinition


def _make_template(
    id: str = "dashboard-analytics",
    name: str = "Analytics Dashboard",
    triggers: tuple[str, ...] = ("dashboard", "analytics"),
    code_gen_type: str = "vue_project",
) -> TemplateDefinition:
    return TemplateDefinition(
        id=id,
        name=name,
        description="Test template",
        code_gen_type=code_gen_type,
        triggers=triggers,
        entry="files/src/App.vue",
        max_prompt_files=3,
        files=(Path("files/src/App.vue"),),
        source_path=Path("/test"),
    )


class TestTemplateSelector:
    def test_select_by_trigger(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(triggers=("dashboard", "后台")))
        selector = TemplateSelector()

        result = selector.select("帮我生成一个后台看板", "vue_project", None, registry)
        assert result is not None
        assert result.id == "dashboard-analytics"

    def test_code_gen_type_filter(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(code_gen_type="vue_project"))
        selector = TemplateSelector()

        result = selector.select("dashboard", "single_file", None, registry)
        assert result is None

    def test_no_match_returns_none(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(triggers=("dashboard",)))
        selector = TemplateSelector()

        result = selector.select("landing page", "vue_project", None, registry)
        assert result is None

    def test_skill_id_bonus(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(id="dashboard", triggers=("dashboard",)))
        registry.register(
            _make_template(
                id="analytics",
                name="Analytics",
                triggers=("analytics",),
            )
        )
        selector = TemplateSelector()

        result = selector.select("dashboard analytics", "vue_project", "dashboard", registry)
        assert result is not None
        assert result.id == "dashboard"

    def test_highest_score_wins(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(id="a", triggers=("dashboard",)))
        registry.register(
            _make_template(id="b", name="B", triggers=("dashboard", "analytics"))
        )
        selector = TemplateSelector()

        result = selector.select("dashboard analytics", "vue_project", None, registry)
        assert result is not None
        assert result.id == "b"

    def test_same_score_alphabetical(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(id="b-template", triggers=("dashboard",)))
        registry.register(
            _make_template(id="a-template", name="A", triggers=("dashboard",))
        )
        selector = TemplateSelector()

        result = selector.select("dashboard", "vue_project", None, registry)
        assert result is not None
        assert result.id == "a-template"

    def test_empty_registry(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        selector = TemplateSelector()

        result = selector.select("dashboard", "vue_project", None, registry)
        assert result is None

    def test_empty_code_gen_type_matches_all(self) -> None:
        from app.capabilities.templates.registry import TemplateRegistry

        registry = TemplateRegistry()
        registry.register(_make_template(code_gen_type=""))
        selector = TemplateSelector()

        result = selector.select("dashboard", "vue_project", None, registry)
        assert result is not None
