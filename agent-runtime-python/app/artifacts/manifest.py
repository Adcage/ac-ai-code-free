import logging
from pathlib import Path
from typing import Any

from app.artifacts.types import ArtifactManifest

logger = logging.getLogger("app.artifacts.manifest")


class ArtifactCollector:
    def __init__(self) -> None:
        self._artifacts: list[ArtifactManifest] = []

    def add(self, artifact: ArtifactManifest) -> None:
        self._artifacts.append(artifact)

    def artifacts(self) -> list[ArtifactManifest]:
        return list(self._artifacts)

    @staticmethod
    def infer_entry(
        code_gen_type: str,
        files_touched: list[str],
        skill_preview_entry: str = "",
        seed_entry: str = "",
        workspace_root: str = "",
    ) -> str:
        if skill_preview_entry:
            return skill_preview_entry
        if seed_entry:
            return seed_entry
        if code_gen_type == "vue_project":
            for f in ("src/App.vue", "index.html"):
                if workspace_root:
                    abs_path = Path(workspace_root) / f
                    if abs_path.exists():
                        return f
                elif f in files_touched:
                    return f
            return "src/App.vue"
        if code_gen_type == "single_file":
            return "index.html"
        return "index.html"

    def build_manifest(
        self,
        code_gen_type: str,
        files_touched: list[str],
        title: str = "",
        skill_preview_entry: str = "",
        seed_entry: str = "",
        source_skill_id: str = "",
        source_skill_ids: list[str] | None = None,
        source_seed_id: str = "",
        source_template_id: str = "",
        source_template_ids: list[str] | None = None,
        design_system_id: str = "",
        craft_ids: list[str] | None = None,
        selection_source: str = "",
        project_mode: str = "",
        metadata: dict[str, Any] | None = None,
        workspace_root: str = "",
    ) -> ArtifactManifest:
        entry = self.infer_entry(
            code_gen_type=code_gen_type,
            files_touched=files_touched,
            skill_preview_entry=skill_preview_entry,
            seed_entry=seed_entry,
            workspace_root=workspace_root,
        )
        manifest = ArtifactManifest(
            version=1,
            kind=code_gen_type,
            title=title or code_gen_type,
            entry=entry,
            code_gen_type=code_gen_type,
            supporting_files=list(files_touched),
            source_skill_id=source_skill_id,
            source_skill_ids=source_skill_ids or [],
            source_seed_id=source_seed_id,
            source_template_id=source_template_id,
            source_template_ids=source_template_ids or [],
            design_system_id=design_system_id,
            craft_ids=craft_ids or [],
            selection_source=selection_source,
            project_mode=project_mode,
            metadata=metadata or {},
        )
        self.add(manifest)
        return manifest
