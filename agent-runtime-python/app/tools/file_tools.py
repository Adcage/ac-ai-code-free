from app.core.exceptions import AgentRuntimeError
from app.tools.workspace import Workspace


PROTECTED_FILES = {"package.json", "vite.config.ts", "vite.config.js", "src/main.ts", "src/main.js"}


class FileTools:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def read_file(self, relative_path: str) -> str:
        path = self.workspace.resolve(relative_path)
        if not path.exists() or not path.is_file():
            raise AgentRuntimeError(f"文件不存在: {relative_path}")
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> str:
        path = self.workspace.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"写入成功: {relative_path}"

    def modify_file(self, relative_path: str, old_text: str, new_text: str) -> str:
        content = self.read_file(relative_path)
        if old_text not in content:
            raise AgentRuntimeError(f"未找到要替换的内容: {relative_path}")
        self.write_file(relative_path, content.replace(old_text, new_text, 1))
        return f"修改成功: {relative_path}"

    def delete_file(self, relative_path: str) -> str:
        normalized = relative_path.replace("\\", "/").lstrip("/")
        if normalized in PROTECTED_FILES:
            raise AgentRuntimeError(f"禁止删除关键文件: {relative_path}")
        path = self.workspace.resolve(relative_path)
        if not path.exists():
            return f"文件不存在，无需删除: {relative_path}"
        if path.is_dir():
            raise AgentRuntimeError(f"不允许删除目录: {relative_path}")
        path.unlink()
        return f"删除成功: {relative_path}"

    def read_dir(self, relative_path: str = ".") -> str:
        path = self.workspace.resolve(relative_path)
        if not path.exists() or not path.is_dir():
            raise AgentRuntimeError(f"目录不存在: {relative_path}")
        return "\n".join(sorted(child.name for child in path.iterdir()))
