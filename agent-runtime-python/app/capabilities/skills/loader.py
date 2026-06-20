import logging
from pathlib import Path

from app.capabilities.common.asset_paths import AssetPathConfig
from app.capabilities.common.frontmatter import parse_frontmatter
from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.skills.types import SkillDefinition

logger = logging.getLogger("app.capabilities.skills.loader")


def _scan_references(skill_dir: Path) -> tuple[str, ...]:
    refs: list[str] = []
    for f in sorted(skill_dir.rglob("*")):
        if f.is_file() and f.name != "SKILL.md":
            ref_path = str(f.relative_to(skill_dir)).replace("\\", "/")
            refs.append(ref_path)
    return tuple(refs)


def _map_frontmatter_to_skill(
    doc_metadata: dict[str, object],
    body: str,
    source_path: Path,
    skill_id: str,
) -> SkillDefinition | None:
    name = doc_metadata.get("name")
    if not isinstance(name, str) or not name:
        logger.warning("Skill asset missing 'name' field: %s", source_path)
        return None

    description = doc_metadata.get("description")
    if not isinstance(description, str):
        description = ""

    known_keys = {"name", "description"}
    metadata = {k: v for k, v in doc_metadata.items() if k not in known_keys}

    references = _scan_references(source_path.parent)

    return SkillDefinition(
        id=skill_id,
        name=name,
        description=description,
        body=body,
        source_path=source_path,
        metadata=metadata,
        references=references,
    )


class SkillLoader:
    def load(self, path_config: AssetPathConfig) -> SkillRegistry:
        registry = SkillRegistry()
        roots = path_config.roots_by_priority()
        seen_ids: set[str] = set()

        for root in roots:
            skills_dir = root / "skills"
            if not skills_dir.is_dir():
                continue

            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue

                skill_file = skill_dir / "SKILL.md"
                if not skill_file.is_file():
                    continue

                skill_id = skill_dir.name
                if skill_id in seen_ids:
                    logger.warning(
                        "Skill id already loaded from higher-priority root, skipping: %s", skill_id
                    )
                    continue

                try:
                    doc = parse_frontmatter(skill_file)
                    skill = _map_frontmatter_to_skill(doc.metadata, doc.body, skill_file, skill_id)
                    if skill is None:
                        continue
                    registry.register(skill)
                    seen_ids.add(skill_id)
                except ValueError as e:
                    logger.error("Duplicate skill id during load: %s - %s", skill_id, e)
                    raise
                except Exception as e:
                    logger.warning("Failed to load skill asset %s: %s", skill_file, e)
                    continue

        logger.info("Loaded %d skill(s)", len(seen_ids))
        return registry
