import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger("app.capabilities.common.frontmatter")


@dataclass(frozen=True)
class FrontmatterDocument:
    metadata: dict[str, object]
    body: str


def parse_frontmatter(path: Path) -> FrontmatterDocument:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip("\n")

    if not stripped.startswith("---"):
        return FrontmatterDocument(metadata={}, body=text)

    first_close = stripped.find("\n---", 3)
    if first_close == -1:
        return FrontmatterDocument(metadata={}, body=text)

    yaml_text = stripped[3:first_close]
    remaining = stripped[first_close + 4 :]

    if remaining.startswith("\n"):
        remaining = remaining[1:]

    try:
        metadata = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        logger.warning("Failed to parse frontmatter YAML in %s", path)
        return FrontmatterDocument(metadata={}, body=text)

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        logger.warning("Frontmatter YAML is not a mapping in %s", path)
        return FrontmatterDocument(metadata={}, body=text)

    return FrontmatterDocument(metadata=metadata, body=remaining)
