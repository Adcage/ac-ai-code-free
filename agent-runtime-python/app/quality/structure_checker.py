import logging
from pathlib import Path
from typing import Callable

from app.artifacts.types import ArtifactManifest
from app.quality.checks import (
    check_ai_default_indigo,
    check_artifact_tags_removed,
    check_entry_exists,
    check_non_empty_files,
    check_placeholder_text,
    check_supporting_files_exist,
    check_vue_app_structure,
    check_vue_state_coverage,
)
from app.quality.result import CheckResult

logger = logging.getLogger("app.quality.structure_checker")


class StructureChecker:
    def __init__(self) -> None:
        self._checks: list[Callable[[str, ArtifactManifest], CheckResult]] = [
            check_entry_exists,
            check_supporting_files_exist,
            check_non_empty_files,
            check_vue_app_structure,
            check_placeholder_text,
            check_artifact_tags_removed,
        ]

    def run(self, workspace_root: str, manifest: ArtifactManifest) -> list[CheckResult]:
        results = []
        for check_fn in self._checks:
            try:
                result = check_fn(workspace_root, manifest)
                results.append(result)
            except Exception as e:
                logger.error("check failed | id=%s error=%s", check_fn.__name__, e, exc_info=True)
                results.append(
                    CheckResult(
                        id=check_fn.__name__,
                        status="fail",
                        severity="error",
                        message=f"Check raised exception: {e}",
                    )
                )

        if manifest.code_gen_type == "vue_project" or any(
            f.endswith(".vue") for f in ([manifest.entry] + manifest.supporting_files)
        ):
            file_paths = [manifest.entry] + [
                f for f in manifest.supporting_files if f != manifest.entry
            ]
            try:
                results.append(check_ai_default_indigo(Path(workspace_root), file_paths))
            except Exception as e:
                logger.error("check failed | id=check_ai_default_indigo error=%s", e, exc_info=True)
                results.append(
                    CheckResult(
                        id="check_ai_default_indigo",
                        status="fail",
                        severity="error",
                        message=f"Check raised exception: {e}",
                    )
                )

            if manifest.code_gen_type == "vue_project":
                try:
                    results.append(check_vue_state_coverage(Path(workspace_root), file_paths))
                except Exception as e:
                    logger.error(
                        "check failed | id=check_vue_state_coverage error=%s", e, exc_info=True
                    )
                    results.append(
                        CheckResult(
                            id="check_vue_state_coverage",
                            status="fail",
                            severity="error",
                            message=f"Check raised exception: {e}",
                        )
                    )

        return results

    @staticmethod
    def determine_manifest_status(results: list[CheckResult]) -> str:
        has_error_fail = False
        has_warning = False
        for r in results:
            if r.status == "fail" and r.severity == "error":
                has_error_fail = True
            elif r.status in ("warn", "fail") and r.severity == "warning":
                has_warning = True
        if has_error_fail:
            return "failed"
        if has_warning:
            return "complete_with_warnings"
        return "complete"
