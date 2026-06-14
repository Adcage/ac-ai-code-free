from pathlib import Path

from app.capabilities.common.asset_paths import AssetPathConfig
from app.capabilities.common.frontmatter import FrontmatterDocument, parse_frontmatter


class TestParseFrontmatter:
    def test_with_metadata(self, tmp_path: Path):
        path = tmp_path / "SKILL.md"
        path.write_text(
            "---\nname: dashboard\ntriggers:\n  - dashboard\n---\n\n# Dashboard Skill\nBody text\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata["name"] == "dashboard"
        assert doc.metadata["triggers"] == ["dashboard"]
        assert "Body text" in doc.body

    def test_without_metadata(self, tmp_path: Path):
        path = tmp_path / "plain.md"
        path.write_text("# Plain\nBody", encoding="utf-8")

        doc = parse_frontmatter(path)

        assert doc.metadata == {}
        assert doc.body == "# Plain\nBody"

    def test_more_closing_dashes(self, tmp_path: Path):
        path = tmp_path / "extra.md"
        path.write_text(
            "---\nname: test\n-----\nBody here\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata["name"] == "test"
        assert "Body here" in doc.body

    def test_empty_file(self, tmp_path: Path):
        path = tmp_path / "empty.md"
        path.write_text("", encoding="utf-8")

        doc = parse_frontmatter(path)

        assert doc.metadata == {}
        assert doc.body == ""

    def test_only_frontmatter_no_body(self, tmp_path: Path):
        path = tmp_path / "nofront.md"
        path.write_text(
            "---\nname: test\n---\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata["name"] == "test"
        assert doc.body == ""

    def test_invalid_yaml_falls_back(self, tmp_path: Path):
        path = tmp_path / "bad.md"
        path.write_text(
            "---\nname: [invalid\n---\nBody\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata == {}
        assert "Body" in doc.body

    def test_frontmatter_scalar_value_falls_back(self, tmp_path: Path):
        path = tmp_path / "scalar.md"
        path.write_text(
            "---\njust a string\n---\nBody\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata == {}
        assert "Body" in doc.body

    def test_leading_newlines_stripped(self, tmp_path: Path):
        path = tmp_path / "leading.md"
        path.write_text(
            "\n\n---\nname: test\n---\nBody\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata["name"] == "test"
        assert "Body" in doc.body

    def test_no_closing_marker(self, tmp_path: Path):
        path = tmp_path / "noclose.md"
        path.write_text(
            "---\nname: test\nno closing marker\n",
            encoding="utf-8",
        )

        doc = parse_frontmatter(path)

        assert doc.metadata == {}
        assert "---" in doc.body

    def test_returns_frozen_document(self, tmp_path: Path):
        path = tmp_path / "frozen.md"
        path.write_text("---\nname: test\n---\nBody", encoding="utf-8")

        doc = parse_frontmatter(path)

        assert isinstance(doc, FrontmatterDocument)


class TestAssetPathConfig:
    def test_roots_by_priority_all(self):
        cfg = AssetPathConfig(
            bundled_root=Path("/bundled"),
            project_root=Path("/project"),
            user_root=Path("/user"),
        )

        assert cfg.roots_by_priority() == (Path("/project"), Path("/user"), Path("/bundled"))

    def test_roots_by_priority_bundled_only(self):
        cfg = AssetPathConfig(bundled_root=Path("/bundled"))

        assert cfg.roots_by_priority() == (Path("/bundled"),)

    def test_roots_by_priority_project_and_bundled(self):
        cfg = AssetPathConfig(bundled_root=Path("/bundled"), project_root=Path("/project"))

        assert cfg.roots_by_priority() == (Path("/project"), Path("/bundled"))

    def test_roots_by_priority_user_and_bundled(self):
        cfg = AssetPathConfig(bundled_root=Path("/bundled"), user_root=Path("/user"))

        assert cfg.roots_by_priority() == (Path("/user"), Path("/bundled"))

    def test_frozen(self):
        cfg = AssetPathConfig(bundled_root=Path("/bundled"))

        try:
            cfg.bundled_root = Path("/other")  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass
