from pathlib import Path

from app.core.exceptions import AgentRuntimeError
from app.core.logging import get_logger

logger = get_logger("app.tools.file_tools")

BLOCKED_SEGMENTS = {".env", ".git", "node_modules", "dist", "__pycache__", ".venv"}


def validate_file_path(file_path: str, workspace_root: Path) -> Path:
    if not file_path:
        raise AgentRuntimeError("文件路径不能为空", code=4001)

    if Path(file_path).is_absolute():
        raise AgentRuntimeError(f"不允许使用绝对路径: {file_path}", code=4002)

    if ".." in Path(file_path).parts:
        raise AgentRuntimeError(f"路径不允许包含 .. : {file_path}", code=4002)

    for segment in Path(file_path).parts:
        if segment in BLOCKED_SEGMENTS:
            raise AgentRuntimeError(f"路径不允许访问 {segment}: {file_path}", code=4003)

    resolved = (workspace_root / file_path).resolve()
    workspace_resolved = workspace_root.resolve()

    if not str(resolved).startswith(str(workspace_resolved)):
        raise AgentRuntimeError(f"路径超出工作区范围: {file_path}", code=4003)

    return resolved


def safe_read_file(file_path: str, workspace_root: Path) -> str:
    resolved = validate_file_path(file_path, workspace_root)
    if not resolved.exists():
        raise AgentRuntimeError(f"文件不存在: {file_path}", code=4004)
    if not resolved.is_file():
        raise AgentRuntimeError(f"路径不是文件: {file_path}", code=4002)
    content = resolved.read_text(encoding="utf-8")
    logger.debug("读取文件: %s (%d bytes)", file_path, len(content))
    return content


def safe_write_file(file_path: str, content: str, workspace_root: Path) -> str:
    resolved = validate_file_path(file_path, workspace_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    logger.info("写入文件: %s (%d bytes)", file_path, len(content))
    return str(resolved)


def safe_delete_file(file_path: str, workspace_root: Path) -> str:
    resolved = validate_file_path(file_path, workspace_root)
    if not resolved.exists():
        raise AgentRuntimeError(f"文件不存在: {file_path}", code=4004)
    resolved.unlink()
    logger.info("删除文件: %s", file_path)
    return str(resolved)


def safe_list_dir(dir_path: str, workspace_root: Path) -> list[str]:
    resolved = validate_file_path(dir_path, workspace_root)
    if not resolved.exists():
        raise AgentRuntimeError(f"目录不存在: {dir_path}", code=4004)
    if not resolved.is_dir():
        raise AgentRuntimeError(f"路径不是目录: {dir_path}", code=4002)
    entries = [str(p.relative_to(resolved)) for p in sorted(resolved.iterdir())]
    logger.debug("列出目录: %s (%d entries)", dir_path, len(entries))
    return entries
