"""文件内容处理器 — 从附件提取文本供 LLM 使用。

仅处理非图片类型的附件。图片由 HistoryBuilder 通过 image_url 方式传给模型。
"""

import io
import logging
import zipfile
import tarfile
from pathlib import PurePosixPath

logger = logging.getLogger("app.agent_loop_vnext.file_processor")

# 单文件提取文本上限
_MAX_TEXT_LENGTH = 32_000

# 压缩包最多列出的文件名数量
_MAX_ARCHIVE_FILES = 50

# 代码文件扩展名 → 语言标签映射
_LANG_MAP: dict[str, str] = {
    ".js": "javascript", ".ts": "typescript", ".py": "python",
    ".java": "java", ".vue": "vue", ".css": "css",
    ".html": "html", ".jsx": "jsx", ".tsx": "tsx",
    ".go": "go", ".rs": "rust", ".c": "c", ".cpp": "cpp",
    ".json": "json", ".xml": "xml", ".yaml": "yaml", ".yml": "yaml",
    ".md": "markdown", ".sql": "sql", ".sh": "bash",
    ".csv": "csv", ".txt": "text", ".toml": "toml",
    ".ini": "ini", ".cfg": "ini", ".conf": "conf",
    ".env": "bash", ".gitignore": "gitignore",
    ".dockerfile": "dockerfile",
}

# MIME → 处理类别
_MIME_CATEGORIES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/msword": "docx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/zip": "archive",
    "application/x-tar": "archive",
    "application/gzip": "archive",
    "text/plain": "text",
    "text/csv": "text",
    "text/markdown": "text",
    "application/json": "text",
    "application/xml": "text",
}


class FileProcessor:
    """从附件内容中提取文本，供 LLM 消费。"""

    def extract_text(self, content: bytes, mime_type: str, file_name: str) -> str | None:
        """入口方法：按类型分派到具体提取方法。

        Args:
            content: 文件原始字节
            mime_type: MIME 类型
            file_name: 原始文件名

        Returns:
            提取的格式化文本，或 None（图片类型）
        """
        if mime_type.startswith("image/"):
            return None

        category = self._categorize(mime_type, file_name)
        match category:
            case "pdf":
                return self._extract_pdf(content, file_name)
            case "docx":
                return self._extract_docx(content, file_name)
            case "archive":
                return self._extract_archive(content, file_name)
            case "text":
                return self._extract_text(content, file_name)
            case _:
                return self._fallback(file_name, mime_type, len(content))

    def _categorize(self, mime_type: str, file_name: str) -> str:
        """将 MIME 类型 + 扩展名归类到处理类别。"""
        if mime_type in _MIME_CATEGORIES:
            return _MIME_CATEGORIES[mime_type]
        # 通过扩展名判断代码/文本文件
        ext = self._ext(file_name)
        if ext in _LANG_MAP:
            return "text"
        # 常见代码扩展名兜底
        code_exts = {".py", ".js", ".ts", ".java", ".vue", ".css", ".html",
                     ".jsx", ".tsx", ".go", ".rs", ".c", ".cpp", ".sh", ".sql",
                     ".md", ".txt", ".json", ".xml", ".yaml", ".yml", ".csv", ".toml"}
        if ext in code_exts:
            return "text"
        return "unknown"

    def _extract_pdf(self, content: bytes, file_name: str) -> str:
        """从 PDF 提取文本。"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            full_text = "\n".join(text_parts)
            return self._format_doc(file_name, self._truncate(full_text))
        except Exception as e:
            logger.warning("PDF 文本提取失败: %s | file=%s", e, file_name)
            return f"[文件: {file_name} — PDF 文本提取失败]"

    def _extract_docx(self, content: bytes, file_name: str) -> str:
        """从 DOCX 提取文本。"""
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
            return self._format_doc(file_name, self._truncate(text))
        except Exception as e:
            logger.warning("DOCX 文本提取失败: %s | file=%s", e, file_name)
            return f"[文件: {file_name} — 文档文本提取失败]"

    def _extract_archive(self, content: bytes, file_name: str) -> str:
        """列出压缩包中的文件名。"""
        try:
            names: list[str] = []
            ext = self._ext(file_name)
            if ext == ".zip":
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    names = zf.namelist()
            elif ext in (".tar", ".gz", ".tgz"):
                with tarfile.open(fileobj=io.BytesIO(content)) as tf:
                    names = tf.getnames()
            else:
                return f"[文件: {file_name} — 不支持的压缩格式]"

            file_list = "\n".join(f"  - {n}" for n in names[:_MAX_ARCHIVE_FILES])
            if len(names) > _MAX_ARCHIVE_FILES:
                file_list += f"\n  ... 共 {len(names)} 个文件"
            return f"📦 压缩包: {file_name}\n包含文件:\n{file_list}"
        except Exception as e:
            logger.warning("压缩包读取失败: %s | file=%s", e, file_name)
            return f"[文件: {file_name} — 压缩包无法读取]"

    def _extract_text(self, content: bytes, file_name: str) -> str:
        """解码纯文本/代码文件。"""
        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            text = content.decode("latin-1", errors="replace")
        text = self._truncate(text)
        ext = self._ext(file_name)
        lang = _LANG_MAP.get(ext, "")
        return self._format_code(file_name, text, lang)

    def _fallback(self, file_name: str, mime_type: str, size: int) -> str:
        """不支持的文件类型占位。"""
        return f"[文件: {file_name} ({mime_type}, {size} bytes) — 内容无法提取]"

    # ==================== 工具方法 ====================

    @staticmethod
    def _ext(file_name: str) -> str:
        """提取小写扩展名（含点号）。"""
        try:
            return PurePosixPath(file_name).suffix.lower()
        except Exception:
            return ""

    @staticmethod
    def _truncate(text: str) -> str:
        """截断过长文本。"""
        if len(text) <= _MAX_TEXT_LENGTH:
            return text
        return text[:_MAX_TEXT_LENGTH] + f"\n\n[...文件内容已截断，原文共 {len(text)} 字符]"

    @staticmethod
    def _format_doc(file_name: str, text: str) -> str:
        """格式化文档提取结果。"""
        return f"---\n📄 文件: {file_name}\n{text}\n---"

    @staticmethod
    def _format_code(file_name: str, text: str, lang: str) -> str:
        """格式化代码/文本提取结果。"""
        return f"---\n📎 文件: {file_name}\n```{lang}\n{text}\n```\n---"
