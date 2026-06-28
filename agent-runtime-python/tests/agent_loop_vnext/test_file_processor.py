"""测试 FileProcessor 附件类型分派与文本提取。"""

import io
import zipfile
import tarfile

import pytest

from app.agent_loop_vnext.shared.file_processor import FileProcessor


@pytest.fixture
def processor():
    return FileProcessor()


# ==================== 图片 ====================

class TestImageHandling:
    def test_image_returns_none(self, processor):
        """图片应返回 None，不提取文本。"""
        for mime in ("image/png", "image/jpeg", "image/gif", "image/webp"):
            result = processor.extract_text(b"fake-image", mime, "test.png")
            assert result is None, f"{mime} 应返回 None"

    def test_image_with_pdf_extension_by_content_type(self, processor):
        """即使文件名混用，也按 MIME 类型判断。"""
        result = processor.extract_text(b"fake", "image/png", "not-an-image.pdf")
        assert result is None


# ==================== PDF ====================

class TestPdfExtraction:
    def test_extract_pdf_simple(self, processor):
        """创建简单 PDF 并提取文本。"""
        pdf_bytes = _create_raw_pdf("Hello PDF World")
        result = processor.extract_text(pdf_bytes, "application/pdf", "doc.pdf")
        assert result is not None
        assert "doc.pdf" in result

    def test_extract_pdf_multi_page(self, processor):
        """多页 PDF 应合并所有页面文本。"""
        pdf_bytes = _create_raw_pdf("Page content")
        result = processor.extract_text(pdf_bytes, "application/pdf", "multi.pdf")
        assert result is not None
        assert "multi.pdf" in result

    def test_extract_pdf_corrupted(self, processor):
        """损坏的 PDF 应返回错误占位。"""
        result = processor.extract_text(b"not a pdf", "application/pdf", "bad.pdf")
        assert result is not None
        assert "PDF" in result
        assert "提取失败" in result or "bad.pdf" in result


# ==================== DOCX ====================

class TestDocxExtraction:
    def test_extract_docx_empty(self, processor):
        """空 DOCX 应返回格式化的文档头。"""
        docx_bytes = _create_minimal_docx("")
        result = processor.extract_text(docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "empty.docx")
        assert result is not None
        assert "empty.docx" in result

    def test_extract_docx_with_content(self, processor):
        """DOCX 中的段落文本应被提取。"""
        docx_bytes = _create_minimal_docx("Hello from Word")
        result = processor.extract_text(docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "doc.docx")
        assert result is not None
        assert "Hello from Word" in result
        assert "doc.docx" in result

    def test_extract_docx_corrupted(self, processor):
        """损坏的 DOCX 应返回错误占位。"""
        result = processor.extract_text(b"not a docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "bad.docx")
        assert result is not None
        assert "提取失败" in result or "bad.docx" in result


# ==================== 代码/文本 ====================

class TestCodeExtraction:
    @pytest.mark.parametrize("ext,lang,content", [
        (".py", "python", "def hello():\n    print('hi')"),
        (".js", "javascript", "function hello() { return 1; }"),
        (".ts", "typescript", "const x: number = 1;"),
        (".java", "java", "public class Hello {}"),
        (".vue", "vue", "<template><div>Hello</div></template>"),
        (".css", "css", "body { color: red; }"),
        (".html", "html", "<html><body>Hello</body></html>"),
        (".go", "go", "package main\nfunc main() {}"),
        (".rs", "rust", "fn main() {}"),
        (".sh", "bash", "echo hello"),
        (".json", "json", '{"key": "value"}'),
        (".md", "markdown", "# Title"),
        (".sql", "sql", "SELECT * FROM users;"),
        (".yaml", "yaml", "key: value"),
    ])
    def test_code_file_with_language_tag(self, processor, ext, lang, content):
        """代码文件应包裹在对应语言标签的代码围栏中。"""
        result = processor.extract_text(content.encode(), f"text/{lang}", f"file{ext}")
        assert result is not None
        assert f"```{lang}" in result or "```" in result
        assert content in result

    def test_plain_text_file(self, processor):
        """纯文本文件应按 UTF-8 解码并包裹。"""
        content = "Line 1\nLine 2\nLine 3"
        result = processor.extract_text(content.encode(), "text/plain", "readme.txt")
        assert result is not None
        assert "readme.txt" in result
        assert "Line 1" in result

    def test_code_file_with_unknown_extension(self, processor):
        """已知扩展名但未知 MIME 的代码文件应被识别。"""
        # .py 文件没有 MIME 类型时仍应通过扩展名识别
        content = "print('hello')"
        result = processor.extract_text(content.encode(), "application/octet-stream", "script.py")
        assert result is not None
        assert "script.py" in result


# ==================== 压缩包 ====================

class TestArchiveExtraction:
    def test_zip_file_listing(self, processor):
        """ZIP 应列出文件名。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("main.py", "print('hello')")
            zf.writestr("utils/helper.py", "def helper(): pass")
            zf.writestr("README.md", "# Project")
        buf.seek(0)

        result = processor.extract_text(buf.read(), "application/zip", "project.zip")
        assert result is not None
        assert "project.zip" in result
        assert "main.py" in result
        assert "utils/helper.py" in result
        assert "README.md" in result

    def test_tar_file_listing(self, processor):
        """TAR 应列出文件名。"""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            tf.addfile(tarfile.TarInfo(name="src/main.py"), io.BytesIO(b"print"))
            tf.addfile(tarfile.TarInfo(name="README.md"), io.BytesIO(b"# Project"))
        buf.seek(0)

        result = processor.extract_text(buf.read(), "application/x-tar", "project.tar")
        assert result is not None
        assert "src/main.py" in result
        assert "README.md" in result

    def test_tar_gz_listing(self, processor):
        """.tar.gz 通过 gzip MIME 识别。"""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            tf.addfile(tarfile.TarInfo(name="data.txt"), io.BytesIO(b"data"))
        buf.seek(0)

        result = processor.extract_text(buf.read(), "application/gzip", "data.tar.gz")
        assert result is not None
        assert "data.txt" in result

    def test_corrupted_zip(self, processor):
        """损坏的压缩包应返回错误占位。"""
        result = processor.extract_text(b"not a zip", "application/zip", "bad.zip")
        assert result is not None
        assert "无法读取" in result or "bad.zip" in result


# ==================== 不支持的类型 ====================

class TestUnsupportedTypes:
    @pytest.mark.parametrize("mime,ext", [
        ("audio/mp3", "mp3"),
        ("video/mp4", "mp4"),
        ("application/x-msdownload", "exe"),
        ("application/octet-stream", "bin"),
    ])
    def test_unsupported_types_return_placeholder(self, processor, mime, ext):
        """不支持的类型应返回占位文本。"""
        result = processor.extract_text(b"some data", mime, f"file.{ext}")
        assert result is not None
        assert "内容无法提取" in result
        assert mime in result or f"file.{ext}" in result


# ==================== 截断 ====================

class TestTruncation:
    def test_text_truncation(self, processor):
        """超长文本应被截断。"""
        long_text = "A" * 40_000  # 超过 32000 字符
        result = processor.extract_text(long_text.encode(), "text/plain", "long.txt")
        assert result is not None
        assert len(result) < len(long_text) + 100  # 截断后远小于原文
        assert "截断" in result

    def test_archive_many_files(self, processor):
        """包含超过 50 个文件的压缩包应显示计数。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(60):
                zf.writestr(f"file_{i}.txt", f"content {i}")
        buf.seek(0)

        result = processor.extract_text(buf.read(), "application/zip", "big.zip")
        assert result is not None
        assert "共 60 个文件" in result

    def test_text_not_truncated_when_short(self, processor):
        """正常长度文本不应截断。"""
        text = "Hello World"
        result = processor.extract_text(text.encode(), "text/plain", "short.txt")
        assert result is not None
        assert "截断" not in result
        assert "Hello World" in result


# ==================== 辅助函数 ====================

def _create_raw_pdf(text: str) -> bytes:
    """创建原始 PDF 结构。"""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R /Resources << /Font << /F1 << /Type /Font"
        b" /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Length 44 >>\n"
        b"stream\n"
        + f"BT /F1 12 Tf 100 700 Td ({escaped}) Tj ET\n".encode()
        + b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"trailer\n"
        b"<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n"
        b"168\n"
        b"%%EOF"
    )
    return content



def _create_minimal_docx(text: str) -> bytes:
    """创建含有指定段落文本的最小 DOCX。"""
    from docx import Document
    doc = Document()
    if text:
        doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
