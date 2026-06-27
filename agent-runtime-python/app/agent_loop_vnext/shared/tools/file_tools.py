"""vNext 文件操作工具集：Read / Write / Edit / Insert / Glob / Grep。

命名对齐 Claude Code CLI 工具风格，Claude 模型训练数据中最熟悉的工具名。
所有 path 参数均为相对于工作区根目录的相对路径。
底层复用 app.tools.file_tools.FileTools 执行实际文件操作。
"""

import logging
import os
import re
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field

from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.tools.file_tools import FileTools

logger = logging.getLogger("app.agent_loop_vnext.shared.tools.file_tools")


# --- 跳过目录和二进制扩展名 ---

_SKIP_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", "dist", ".venv", ".idea", ".vscode",
    ".next", ".nuxt", "build", "coverage", ".cache",
})

_BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".lock", ".pyc", ".pyo", ".so", ".dll", ".exe",
})


# --- Input Schemas ---

class ReadInput(BaseModel):
    path: str = Field(description="文件或目录的相对路径，例如 src/App.vue")
    view_range: list[int] | None = Field(
        default=None,
        description="查看的行范围 [start, end]，1-indexed，end=-1 表示到文件末尾。仅查看文件时有效。",
    )


class WriteInput(BaseModel):
    path: str = Field(description="要创建的文件相对路径，例如 src/App.vue。文件已存在则报错。")
    content: str = Field(description="文件内容")


class EditInput(BaseModel):
    path: str = Field(description="要修改的文件相对路径，例如 src/App.vue")
    old_str: str = Field(description="要替换的原始文本，必须精确匹配（包括缩进和空格）")
    new_str: str = Field(description="替换后的新文本")


class InsertInput(BaseModel):
    path: str = Field(description="要修改的文件相对路径，例如 src/App.vue")
    insert_line: int = Field(description="在第几行之后插入，0 表示文件开头")
    insert_text: str = Field(description="要插入的文本")


class GlobInput(BaseModel):
    pattern: str = Field(description="glob 模式，例如 **/*.vue 或 src/**/*.ts")
    path: str = Field(default=".", description="搜索的起始目录，默认为工作区根目录")


class GrepInput(BaseModel):
    pattern: str = Field(description="正则表达式搜索模式")
    path: str = Field(default=".", description="搜索的起始目录，默认为工作区根目录")
    include: str = Field(default="", description="文件名过滤模式，例如 *.vue 或 *.{ts,tsx}")


# --- Tools ---

class ReadTool(AgentTool):
    name: str = "Read"
    description: str = "查看文件内容或列出目录结构。目录为空时返回'目录为空'，文件为空时返回'文件内容为空'。"
    args_schema: Type[BaseModel] = ReadInput
    file_tools: FileTools | None = None

    async def _arun(self, path: str, view_range: list[int] | None = None) -> str:
        abs_path = self.file_tools._workspace.resolve(path)

        if os.path.isdir(abs_path):
            result = await self.file_tools.read_dir(path)
            return result if result else "目录为空"

        if not os.path.exists(abs_path):
            from app.core.error_codes import AgentErrorCode
            from app.core.exceptions import AgentRuntimeError

            raise AgentRuntimeError(
                f"文件不存在: {path}", code=AgentErrorCode.TOOL_CALL_FAILED
            )

        content = await self.file_tools.read_file(path)
        if not content.strip():
            return "文件内容为空"

        if view_range and len(view_range) == 2:
            lines = content.splitlines()
            start, end = view_range
            if end == -1 or end > len(lines):
                end = len(lines)
            if start < 1:
                start = 1
            content = "\n".join(lines[start - 1:end])

        return content


class WriteTool(AgentTool):
    name: str = "Write"
    description: str = "创建新文件。如果文件已存在则报错。"
    args_schema: Type[BaseModel] = WriteInput
    file_tools: FileTools | None = None

    async def _arun(self, path: str, content: str) -> str:
        abs_path = self.file_tools._workspace.resolve(path)
        if os.path.exists(abs_path):
            from app.core.error_codes import AgentErrorCode
            from app.core.exceptions import AgentRuntimeError

            raise AgentRuntimeError(
                f"文件已存在: {path}", code=AgentErrorCode.TOOL_CALL_FAILED
            )
        return await self.file_tools.write_file(path, content)


class EditTool(AgentTool):
    name: str = "Edit"
    description: str = "替换文件中精确匹配的文本。用于对已有文件做精细修改。old_str 必须精确匹配（包括缩进和空格）。"
    args_schema: Type[BaseModel] = EditInput
    file_tools: FileTools | None = None

    async def _arun(self, path: str, old_str: str, new_str: str) -> str:
        if not old_str:
            from app.core.error_codes import AgentErrorCode
            from app.core.exceptions import AgentRuntimeError

            raise AgentRuntimeError(
                "old_str 不能为空", code=AgentErrorCode.TOOL_CALL_FAILED
            )

        return await self.file_tools.modify_file(path, old_str, new_str)


class InsertTool(AgentTool):
    name: str = "Insert"
    description: str = "在文件的指定行号后插入文本。0 表示在文件开头插入。"
    args_schema: Type[BaseModel] = InsertInput
    file_tools: FileTools | None = None

    async def _arun(self, path: str, insert_line: int, insert_text: str) -> str:
        from app.core.error_codes import AgentErrorCode
        from app.core.exceptions import AgentRuntimeError

        abs_path = self.file_tools._workspace.resolve(path)
        if not os.path.exists(abs_path):
            raise AgentRuntimeError(
                f"文件不存在: {path}", code=AgentErrorCode.TOOL_CALL_FAILED
            )

        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)
        if insert_line < 0 or insert_line > total_lines:
            raise AgentRuntimeError(
                f"insert_line {insert_line} 超出文件行数范围 (0-{total_lines})",
                code=AgentErrorCode.TOOL_CALL_FAILED,
            )

        lines.insert(insert_line, insert_text.rstrip("\n") + "\n")

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info("insert | path=%s line=%d len=%d", path, insert_line, len(insert_text))
        return f"插入成功: {path}"


class GlobTool(AgentTool):
    name: str = "Glob"
    description: str = (
        "根据文件名模式快速搜索匹配的文件路径。"
        "支持 glob 语法：* 匹配任意非分隔符字符，** 匹配任意深度目录。"
        "结果按修改时间排序（最新优先），最多返回 100 个。"
    )
    args_schema: Type[BaseModel] = GlobInput
    file_tools: FileTools | None = None

    _MAX_RESULTS = 100

    async def _arun(self, pattern: str, path: str = ".") -> str:
        workspace = self.file_tools._workspace
        # 路径安全校验
        search_root = workspace.resolve(path)
        if not os.path.isdir(search_root):
            from app.core.error_codes import AgentErrorCode
            from app.core.exceptions import AgentRuntimeError

            raise AgentRuntimeError(
                f"路径不是目录: {path}", code=AgentErrorCode.TOOL_CALL_FAILED
            )

        results: list[tuple[float, str]] = []  # (mtime, relative_path)

        for match in Path(search_root).glob(pattern):
            if not match.is_file():
                continue
            # 跳过忽略目录下的文件
            if self._is_in_skipped_dir(match, search_root):
                continue
            # 路径安全二次校验
            resolved = str(match.resolve())
            if not resolved.startswith(str(Path(workspace.root).resolve())):
                continue
            rel_path = os.path.relpath(match, workspace.root).replace(os.sep, "/")
            try:
                mtime = match.stat().st_mtime
            except OSError:
                mtime = 0.0
            results.append((mtime, rel_path))

        # 按修改时间倒序
        results.sort(key=lambda x: x[0], reverse=True)

        # 截断
        truncated = len(results) > self._MAX_RESULTS
        results = results[:self._MAX_RESULTS]

        if not results:
            return "未找到匹配的文件"

        lines = [r[1] for r in results]
        output = "\n".join(lines)
        if truncated:
            output += f"\n\n(结果已截断，共 {len(results)} 个。请使用更精确的模式缩小范围。)"
        return output

    @staticmethod
    def _is_in_skipped_dir(path: Path, search_root: Path) -> bool:
        """检查文件是否在跳过目录内。"""
        try:
            rel = path.relative_to(search_root)
        except ValueError:
            return True
        parts = rel.parts
        return any(part in _SKIP_DIRS for part in parts)


class GrepTool(AgentTool):
    name: str = "Grep"
    description: str = (
        "在文件内容中搜索匹配正则表达式的文本。"
        "返回匹配的文件路径、行号和内容。支持完整正则语法。"
        "最多返回 50 个匹配结果。"
    )
    args_schema: Type[BaseModel] = GrepInput
    file_tools: FileTools | None = None

    _MAX_RESULTS = 50
    _MAX_LINE_LENGTH = 200

    async def _arun(self, pattern: str, path: str = ".", include: str = "") -> str:
        from app.core.error_codes import AgentErrorCode
        from app.core.exceptions import AgentRuntimeError

        workspace = self.file_tools._workspace
        # 路径安全校验
        search_root = workspace.resolve(path)
        if not os.path.isdir(search_root):
            raise AgentRuntimeError(
                f"路径不是目录: {path}", code=AgentErrorCode.TOOL_CALL_FAILED
            )

        # 编译正则
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise AgentRuntimeError(
                f"正则表达式无效: {e}", code=AgentErrorCode.TOOL_CALL_FAILED
            )

        # 构建文件名过滤函数
        include_patterns = self._parse_include_patterns(include)

        results: list[str] = []
        root_path = Path(search_root)

        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            # 跳过忽略目录
            if GlobTool._is_in_skipped_dir(file_path, root_path):
                continue
            # 跳过二进制文件
            if file_path.suffix.lower() in _BINARY_EXTENSIONS:
                continue
            # 文件名过滤
            if not self._matches_include(file_path, include_patterns):
                continue
            # 路径安全二次校验
            resolved = str(file_path.resolve())
            if not resolved.startswith(str(Path(workspace.root).resolve())):
                continue

            # 逐行搜索
            rel_path = os.path.relpath(file_path, workspace.root).replace(os.sep, "/")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        if regex.search(line):
                            display_line = self._truncate_line(line.rstrip("\n"))
                            results.append(f"{rel_path}:{line_no}: {display_line}")
                            if len(results) >= self._MAX_RESULTS:
                                break
                if len(results) >= self._MAX_RESULTS:
                    break
            except (PermissionError, OSError):
                continue

        if not results:
            return "未找到匹配的内容"

        truncated = len(results) >= self._MAX_RESULTS
        output = "\n".join(results)
        if truncated:
            output += f"\n\n(结果已截断至 {self._MAX_RESULTS} 个。请使用更精确的模式或指定 include 缩小范围。)"
        return output

    @staticmethod
    def _parse_include_patterns(include: str) -> list[str]:
        """解析 include 参数为多个 glob 模式。"""
        if not include:
            return []
        # 支持 {ts,tsx} 大括号展开
        if "{" in include and "}" in include:
            start = include.index("{")
            end = include.index("}")
            variants = include[start + 1:end].split(",")
            return [include[:start] + v.strip() + include[end + 1:] for v in variants]
        return [include]

    @staticmethod
    def _matches_include(file_path: Path, patterns: list[str]) -> bool:
        """检查文件是否匹配 include 过滤模式。"""
        if not patterns:
            return True
        from fnmatch import fnmatch
        name = file_path.name
        return any(fnmatch(name, p) for p in patterns)

    def _truncate_line(self, line: str) -> str:
        """截断过长的行。"""
        if len(line) <= self._MAX_LINE_LENGTH:
            return line
        half = self._MAX_LINE_LENGTH // 2 - 2
        return line[:half] + " ... " + line[-half:]
