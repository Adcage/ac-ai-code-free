import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger("app.agent_loop.tools.run_checks")


class RunChecksInput(BaseModel):
    pass  # 无需参数，自动从 state 和 context 获取


class RunChecksTool(BaseTool):
    """封装 StructureChecker 为可供 AI 调用的只读工具。
    结果缓存到 state.validation_check_results，不会重复执行。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "run_checks"
    description: str = "执行项目结构校验，返回检查结果列表。包括入口文件存在性、文件完整性、Vue 项目结构等检查。"
    args_schema: type[BaseModel] = RunChecksInput

    _state: object | None = None
    _workspace_root: str = ""
    _quality_checker: object | None = None

    def set_state(self, state) -> None:
        self._state = state

    def set_workspace(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    def set_quality_checker(self, checker) -> None:
        self._quality_checker = checker

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self) -> str:
        state = self._state

        # 如果已经执行过，返回缓存结果
        if getattr(state, "validation_check_results", None) is not None:
            return "校验结果（已缓存）：\n" + self._format_results(state.validation_check_results)

        if not self._workspace_root or self._quality_checker is None:
            return "校验工具未正确配置，无法执行检查。"

        # 构建 ArtifactManifest
        from app.artifacts.manifest import ArtifactCollector

        code_gen_type = ""
        # 优先使用推荐的类型
        recommended = getattr(state, "recommended_code_gen_type", None)
        if recommended:
            code_gen_type = recommended
        else:
            # 从 _context 获取
            ctx = getattr(state, "_context", None)
            if ctx and hasattr(ctx, "code_gen_type"):
                cgt = getattr(ctx, "code_gen_type", None)
                code_gen_type = cgt.value if cgt else ""

        files_touched = getattr(state, "files_touched", [])

        try:
            manifest = ArtifactCollector().build_manifest(
                code_gen_type=code_gen_type,
                files_touched=files_touched,
                workspace_root=self._workspace_root,
            )
        except Exception as e:
            logger.warning("run_checks | manifest build failed: %s", e)
            return f"无法构建 manifest：{e}"

        # 执行 StructureChecker
        try:
            results = self._quality_checker.run(self._workspace_root, manifest)
        except Exception as e:
            logger.error("run_checks | checker failed: %s", e, exc_info=True)
            return f"校验执行失败：{e}"

        # 缓存结果到 state（仅执行一次）
        state.validation_check_results = [
            {"id": r.id, "status": r.status, "severity": r.severity, "message": r.message}
            for r in results
        ]

        logger.info(
            "run_checks | results=%d pass=%d fail=%d",
            len(results),
            sum(1 for r in results if r.status == "pass"),
            sum(1 for r in results if r.status == "fail"),
        )

        return "校验结果：\n" + self._format_results(state.validation_check_results)

    @staticmethod
    def _format_results(results: list[dict]) -> str:
        lines = []
        for r in results:
            icon = "✓" if r.get("status") == "pass" else ("✗" if r.get("status") == "fail" else "⚠")
            lines.append(f"{icon} [{r.get('severity', '?')}] {r.get('id', '?')}: {r.get('message', '')}")
        return "\n".join(lines)
