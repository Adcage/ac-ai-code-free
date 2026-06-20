import logging
from pathlib import Path

from app.capabilities.seeds.types import SeedDefinition

logger = logging.getLogger("app.capabilities.seeds.applier")


def _is_path_traversal(relative_path: str) -> bool:
    parts = Path(relative_path).parts
    if any(part == ".." for part in parts):
        return True
    if relative_path.startswith("/") or relative_path.startswith("\\"):
        return True
    p = Path(relative_path)
    try:
        if p.is_absolute():
            return True
    except ValueError:
        return True
    return False


class SeedApplier:
    def apply(self, seed: SeedDefinition, workspace_path: Path) -> list[str]:
        if not seed.files_dir.is_dir():
            logger.warning("Seed files_dir does not exist: %s", seed.files_dir)
            return []

        copied: list[str] = []
        files_dir = seed.files_dir

        for file_path in sorted(files_dir.rglob("*")):
            if not file_path.is_file():
                continue

            relative = file_path.relative_to(files_dir)
            relative_str = str(relative)

            if _is_path_traversal(relative_str):
                logger.warning("Path traversal detected, skipping: %s", relative_str)
                continue

            target = workspace_path / relative

            if seed.copy_mode == "missing-only" and target.exists():
                continue

            target.parent.mkdir(parents=True, exist_ok=True)

            try:
                content = file_path.read_bytes()
                target.write_bytes(content)
                copied.append(relative_str)
            except OSError as e:
                logger.warning("Failed to copy seed file %s: %s", relative_str, e)
                continue

        logger.info("Applied seed '%s': copied %d file(s)", seed.id, len(copied))
        return copied
