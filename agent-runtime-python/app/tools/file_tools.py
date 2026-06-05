from pathlib import Path

BLOCKED_SEGMENTS = {".env", ".git", "node_modules", "dist", "__pycache__", ".venv"}


class FileSecurityError(Exception):
    pass


def validate_file_path(file_path: str, workspace_root: Path) -> Path:
    if not file_path:
        raise FileSecurityError("文件路径不能为空")

    if Path(file_path).is_absolute():
        raise FileSecurityError(f"不允许使用绝对路径: {file_path}")

    if ".." in Path(file_path).parts:
        raise FileSecurityError(f"路径不允许包含 .. : {file_path}")

    for segment in Path(file_path).parts:
        if segment in BLOCKED_SEGMENTS:
            raise FileSecurityError(f"路径不允许访问 {segment}: {file_path}")

    resolved = (workspace_root / file_path).resolve()
    workspace_resolved = workspace_root.resolve()

    if not str(resolved).startswith(str(workspace_resolved)):
        raise FileSecurityError(f"路径超出工作区范围: {file_path}")

    return resolved


def safe_read_file(file_path: str, workspace_root: Path) -> str:
    resolved = validate_file_path(file_path, workspace_root)
    if not resolved.exists():
        raise FileSecurityError(f"文件不存在: {file_path}")
    if not resolved.is_file():
        raise FileSecurityError(f"路径不是文件: {file_path}")
    return resolved.read_text(encoding="utf-8")


def safe_write_file(file_path: str, content: str, workspace_root: Path) -> str:
    resolved = validate_file_path(file_path, workspace_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return str(resolved)


def safe_delete_file(file_path: str, workspace_root: Path) -> str:
    resolved = validate_file_path(file_path, workspace_root)
    if not resolved.exists():
        raise FileSecurityError(f"文件不存在: {file_path}")
    resolved.unlink()
    return str(resolved)


def safe_list_dir(dir_path: str, workspace_root: Path) -> list[str]:
    resolved = validate_file_path(dir_path, workspace_root)
    if not resolved.exists():
        raise FileSecurityError(f"目录不存在: {dir_path}")
    if not resolved.is_dir():
        raise FileSecurityError(f"路径不是目录: {dir_path}")
    return [str(p.relative_to(resolved)) for p in sorted(resolved.iterdir())]
