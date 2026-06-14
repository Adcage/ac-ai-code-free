import logging

from app.artifacts.types import ArtifactCheckResult, ArtifactManifest
from app.artifacts.writer import ArtifactWriter
from app.nodes.base import NodeMetadata, RuntimeNode
from app.quality.result import CheckResult
from app.quality.structure_checker import StructureChecker
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.structure_check")


class StructureCheckNode(RuntimeNode):
    metadata = NodeMetadata(id="structure_check", name="结构检查", description="对生成的产物执行确定性结构检查")

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        workspace_root = context.workspace_path

        manifest = self._load_manifest(workspace_root)
        if manifest is None:
            logger.warning("structure_check skipped | no manifest found")
            await services.event_bus.emit(
                RuntimeEvent(RuntimeEventType.NODE_COMPLETED, {"node_id": "structure_check"})
            )
            return state

        checker = services.quality_checker
        if checker is None:
            checker = StructureChecker()

        results: list[CheckResult] = checker.run(workspace_root, manifest)

        state.quality_results = [
            {
                "id": r.id,
                "status": r.status,
                "severity": r.severity,
                "message": r.message,
                "file_path": r.file_path,
            }
            for r in results
        ]

        manifest.checks = [
            ArtifactCheckResult(id=r.id, status=r.status, message=r.message, severity=r.severity)
            for r in results
        ]
        manifest.status = StructureChecker.determine_manifest_status(results)

        artifact_writer = services.artifact_writer
        if artifact_writer is not None:
            artifact_writer.write(workspace_root, manifest)

        logger.info(
            "structure_check done | status=%s checks=%d",
            manifest.status,
            len(results),
        )

        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.NODE_COMPLETED, {"node_id": "structure_check"})
        )

        return state

    @staticmethod
    def _load_manifest(workspace_root: str) -> ArtifactManifest | None:
        return ArtifactWriter.read(workspace_root)
