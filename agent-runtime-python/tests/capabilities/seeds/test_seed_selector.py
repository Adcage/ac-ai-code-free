from pathlib import Path

from app.capabilities.seeds.registry import SeedRegistry
from app.capabilities.seeds.selector import SeedSelector
from app.capabilities.seeds.types import SeedDefinition


def _make_seed(
    id: str,
    name: str,
    code_gen_type: str = "vue_project",
    triggers: tuple[str, ...] = (),
    copy_mode: str = "missing-only",
) -> SeedDefinition:
    return SeedDefinition(
        id=id,
        name=name,
        description=f"{name} seed",
        code_gen_type=code_gen_type,
        triggers=triggers,
        entry="src/App.vue",
        files_dir=Path(f"/seeds/{id}/files"),
        copy_mode=copy_mode,
        source_path=Path(f"/seeds/{id}/seed.json"),
    )


class TestSeedSelector:
    def test_generate_vue_project_defaults_to_vue_basic(self):
        registry = SeedRegistry()
        registry.register(_make_seed("vue-basic", "Vue Basic"))

        selector = SeedSelector()
        result = selector.select("随便什么prompt", "vue_project", "generate", registry)

        assert result is not None
        assert result.id == "vue-basic"

    def test_modify_mode_returns_none(self):
        registry = SeedRegistry()
        registry.register(_make_seed("vue-basic", "Vue Basic"))

        selector = SeedSelector()
        result = selector.select("生成一个vue应用", "vue_project", "modify", registry)

        assert result is None

    def test_trigger_match_selects_matching_seed(self):
        registry = SeedRegistry()
        registry.register(_make_seed("vue-basic", "Vue Basic", triggers=("vue", "前端")))
        registry.register(
            _make_seed("vue-dashboard", "Vue Dashboard", triggers=("dashboard", "后台", "管理后台"))
        )

        selector = SeedSelector()
        result = selector.select("帮我生成一个后台管理界面", "vue_project", "generate", registry)

        assert result is not None
        assert result.id == "vue-dashboard"

    def test_code_gen_type_mismatch_excluded(self):
        registry = SeedRegistry()
        registry.register(_make_seed("vue-basic", "Vue Basic", code_gen_type="vue_project"))

        selector = SeedSelector()
        result = selector.select("生成页面", "single_file", "generate", registry)

        assert result is None

    def test_no_matching_seed_for_non_vue_project(self):
        registry = SeedRegistry()
        registry.register(_make_seed("vue-basic", "Vue Basic", code_gen_type="vue_project"))

        selector = SeedSelector()
        result = selector.select("生成页面", "multi-file", "generate", registry)

        assert result is None

    def test_empty_registry_returns_none(self):
        registry = SeedRegistry()
        selector = SeedSelector()
        result = selector.select("生成vue应用", "vue_project", "generate", registry)

        assert result is None

    def test_vue_basic_default_not_found_returns_none(self):
        registry = SeedRegistry()
        registry.register(
            _make_seed("vue-dashboard", "Vue Dashboard", triggers=("dashboard",))
        )

        selector = SeedSelector()
        result = selector.select("随便什么", "vue_project", "generate", registry)

        assert result is None

    def test_same_score_alphabetical_tiebreak(self):
        registry = SeedRegistry()
        registry.register(_make_seed("zebra-seed", "Zebra", triggers=("vue",)))
        registry.register(_make_seed("alpha-seed", "Alpha", triggers=("vue",)))

        selector = SeedSelector()
        result = selector.select("vue应用", "vue_project", "generate", registry)

        assert result is not None
        assert result.id == "alpha-seed"

    def test_route_mode_returns_none(self):
        registry = SeedRegistry()
        registry.register(_make_seed("vue-basic", "Vue Basic"))

        selector = SeedSelector()
        result = selector.select("vue应用", "vue_project", "route", registry)

        assert result is None
