"""测试 vNext 文件操作工具。"""

import tempfile
from pathlib import Path

import pytest

from app.agent_loop_vnext.shared.tools.file_tools import (
    EditTool,
    GlobTool,
    GrepTool,
    InsertTool,
    ReadTool,
    WriteTool,
)
from app.tools.file_tools import FileTools, Workspace


@pytest.fixture
def workspace():
    """创建临时工作区。"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Workspace(tmp)


@pytest.fixture
def file_tools(workspace):
    """创建 FileTools 实例。"""
    return FileTools(workspace)


# --- Read ---

@pytest.mark.asyncio
async def test_read_dir(file_tools, workspace):
    """Read 目录应返回目录列表。"""
    tool = ReadTool(file_tools=file_tools)
    Path(workspace.root, "hello.txt").write_text("hello", encoding="utf-8")
    result = await tool._arun(".")
    assert "hello.txt" in result


@pytest.mark.asyncio
async def test_read_empty_dir(file_tools):
    """空目录应返回"目录为空"。"""
    tool = ReadTool(file_tools=file_tools)
    result = await tool._arun(".")
    assert result == "目录为空"


@pytest.mark.asyncio
async def test_read_file(file_tools, workspace):
    """Read 文件应返回文件内容。"""
    Path(workspace.root, "test.txt").write_text("hello world", encoding="utf-8")
    tool = ReadTool(file_tools=file_tools)
    result = await tool._arun("test.txt")
    assert result == "hello world"


@pytest.mark.asyncio
async def test_read_empty_file(file_tools, workspace):
    """空文件应返回"文件内容为空"。"""
    Path(workspace.root, "empty.txt").write_text("", encoding="utf-8")
    tool = ReadTool(file_tools=file_tools)
    result = await tool._arun("empty.txt")
    assert "文件内容为空" in result


@pytest.mark.asyncio
async def test_read_file_with_view_range(file_tools, workspace):
    """Read 文件支持 view_range 截取行范围。"""
    Path(workspace.root, "lines.txt").write_text(
        "line1\nline2\nline3\nline4\nline5\n", encoding="utf-8"
    )
    tool = ReadTool(file_tools=file_tools)
    result = await tool._arun("lines.txt", view_range=[2, 4])
    lines = result.strip().split("\n")
    assert lines == ["line2", "line3", "line4"]


# --- Write ---

@pytest.mark.asyncio
async def test_write_file(file_tools, workspace):
    """Write 应创建新文件。"""
    tool = WriteTool(file_tools=file_tools)
    result = await tool._arun("new.txt", "new content")
    assert "写入成功" in result
    content = Path(workspace.root, "new.txt").read_text(encoding="utf-8")
    assert content == "new content"


@pytest.mark.asyncio
async def test_write_file_already_exists(file_tools, workspace):
    """Write 已存在文件应报错。"""
    Path(workspace.root, "exist.txt").write_text("existing", encoding="utf-8")
    tool = WriteTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("exist.txt", "new content")
    assert "文件已存在" in str(exc.value)


# --- Edit ---

@pytest.mark.asyncio
async def test_edit_replace(file_tools, workspace):
    """Edit 应精确替换文本。"""
    Path(workspace.root, "test.txt").write_text("hello world", encoding="utf-8")
    tool = EditTool(file_tools=file_tools)
    result = await tool._arun("test.txt", "hello", "hi")
    assert "修改成功" in result
    content = Path(workspace.root, "test.txt").read_text(encoding="utf-8")
    assert content == "hi world"


@pytest.mark.asyncio
async def test_edit_not_found(file_tools, workspace):
    """Edit 未找到 old_str 应报错。"""
    Path(workspace.root, "test.txt").write_text("hello world", encoding="utf-8")
    tool = EditTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("test.txt", "not_exist", "hi")
    assert "未找到" in str(exc.value)


@pytest.mark.asyncio
async def test_edit_empty_old_str(file_tools, workspace):
    """Edit 的 old_str 为空应报错。"""
    Path(workspace.root, "test.txt").write_text("hello", encoding="utf-8")
    tool = EditTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("test.txt", "", "hi")
    assert "不能为空" in str(exc.value)


# --- Insert ---

@pytest.mark.asyncio
async def test_insert(file_tools, workspace):
    """Insert 应在指定行后插入文本。"""
    Path(workspace.root, "test.txt").write_text("line1\nline2\nline3\n", encoding="utf-8")
    tool = InsertTool(file_tools=file_tools)
    result = await tool._arun("test.txt", 1, "inserted_line")
    assert "插入成功" in result
    content = Path(workspace.root, "test.txt").read_text(encoding="utf-8")
    assert "inserted_line" in content
    lines = content.strip().split("\n")
    assert lines[1] == "inserted_line"


@pytest.mark.asyncio
async def test_insert_at_beginning(file_tools, workspace):
    """insert_line=0 表示在文件开头插入。"""
    Path(workspace.root, "test.txt").write_text("line1\nline2\n", encoding="utf-8")
    tool = InsertTool(file_tools=file_tools)
    await tool._arun("test.txt", 0, "header")
    content = Path(workspace.root, "test.txt").read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert lines[0] == "header"


@pytest.mark.asyncio
async def test_insert_line_out_of_range(file_tools, workspace):
    """insert_line 超范围应报错。"""
    Path(workspace.root, "test.txt").write_text("line1\nline2\n", encoding="utf-8")
    tool = InsertTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("test.txt", 999, "new")
    assert "超出" in str(exc.value)


# --- Glob ---

@pytest.mark.asyncio
async def test_glob_finds_files_by_pattern(file_tools, workspace):
    """Glob 应根据模式找到文件。"""
    Path(workspace.root, "app.ts").write_text("// ts", encoding="utf-8")
    sub = Path(workspace.root, "src")
    sub.mkdir()
    Path(sub, "index.ts").write_text("// index", encoding="utf-8")
    Path(sub, "style.css").write_text("/* css */", encoding="utf-8")

    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("**/*.ts")
    assert "app.ts" in result
    assert "src/index.ts" in result
    assert "style.css" not in result


@pytest.mark.asyncio
async def test_glob_respects_path_parameter(file_tools, workspace):
    """Glob 指定 path 只在子目录搜。"""
    sub = Path(workspace.root, "src")
    sub.mkdir()
    Path(sub, "a.ts").write_text("// a", encoding="utf-8")
    Path(workspace.root, "b.ts").write_text("// b", encoding="utf-8")

    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("*.ts", path="src")
    assert "src/a.ts" in result
    assert "b.ts" not in result


@pytest.mark.asyncio
async def test_glob_returns_empty_for_no_match(file_tools, workspace):
    """Glob 无匹配返回提示。"""
    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("*.xyz")
    assert "未找到" in result


@pytest.mark.asyncio
async def test_glob_truncates_at_max_results(file_tools, workspace):
    """Glob 结果超 100 截断。"""
    for i in range(150):
        Path(workspace.root, f"file_{i:03d}.txt").write_text(str(i), encoding="utf-8")

    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("*.txt")
    assert "截断" in result


@pytest.mark.asyncio
async def test_glob_skips_ignored_directories(file_tools, workspace):
    """Glob 跳过 node_modules 等忽略目录。"""
    nm = Path(workspace.root, "node_modules")
    nm.mkdir()
    Path(nm, "package.js").write_text("// pkg", encoding="utf-8")
    Path(workspace.root, "app.js").write_text("// app", encoding="utf-8")

    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("**/*.js")
    assert "app.js" in result
    assert "node_modules" not in result


@pytest.mark.asyncio
async def test_glob_rejects_path_traversal(file_tools, workspace):
    """Glob 路径穿越应报错。"""
    tool = GlobTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("*.txt", path="../../etc")
    assert "穿越" in str(exc.value)


# --- Grep ---

@pytest.mark.asyncio
async def test_grep_finds_matching_lines(file_tools, workspace):
    """Grep 应找到匹配行并返回路径和行号。"""
    Path(workspace.root, "app.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    Path(workspace.root, "util.py").write_text("def world():\n    pass\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("def hello")
    assert "app.py" in result
    assert "1" in result


@pytest.mark.asyncio
async def test_grep_respects_path_parameter(file_tools, workspace):
    """Grep 指定 path 只在子目录搜。"""
    sub = Path(workspace.root, "src")
    sub.mkdir()
    Path(sub, "a.py").write_text("target_func()\n", encoding="utf-8")
    Path(workspace.root, "b.py").write_text("target_func()\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("target_func", path="src")
    assert "src/a.py" in result
    assert "b.py" not in result


@pytest.mark.asyncio
async def test_grep_respects_include_filter(file_tools, workspace):
    """Grep include 参数过滤文件类型。"""
    Path(workspace.root, "app.py").write_text("const x = 1\n", encoding="utf-8")
    Path(workspace.root, "app.ts").write_text("const x = 1\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("const x", include="*.py")
    assert "app.py" in result
    assert "app.ts" not in result


@pytest.mark.asyncio
async def test_grep_returns_empty_for_no_match(file_tools, workspace):
    """Grep 无匹配返回提示。"""
    Path(workspace.root, "test.py").write_text("hello world\n", encoding="utf-8")
    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("xyz_not_exist_123")
    assert "未找到" in result


@pytest.mark.asyncio
async def test_grep_truncates_at_max_results(file_tools, workspace):
    """Grep 结果超 50 截断。"""
    for i in range(60):
        Path(workspace.root, f"file_{i:03d}.py").write_text(f"match_target_{i}\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("match_target")
    assert "截断" in result


@pytest.mark.asyncio
async def test_grep_skips_binary_and_ignored_dirs(file_tools, workspace):
    """Grep 跳过二进制文件和忽略目录。"""
    nm = Path(workspace.root, "node_modules")
    nm.mkdir()
    Path(nm, "pkg.js").write_text("secret_token\n", encoding="utf-8")
    Path(workspace.root, "app.py").write_text("secret_token\n", encoding="utf-8")
    Path(workspace.root, "image.png").write_bytes(b"secret_token")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("secret_token")
    assert "app.py" in result
    assert "node_modules" not in result
    assert "image.png" not in result


@pytest.mark.asyncio
async def test_grep_rejects_path_traversal(file_tools, workspace):
    """Grep 路径穿越应报错。"""
    tool = GrepTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("pattern", path="../../etc")
    assert "穿越" in str(exc.value)


@pytest.mark.asyncio
async def test_grep_handles_encoding_errors(file_tools, workspace):
    """Grep 遇到非 UTF-8 文件不崩溃。"""
    Path(workspace.root, "binary.bin").write_bytes(b"\xff\xfe invalid utf8 \x00")
    Path(workspace.root, "normal.py").write_text("hello\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("hello")
    assert "normal.py" in result


# --- Read 边界 ---

@pytest.mark.asyncio
async def test_read_nonexistent_file(file_tools, workspace):
    """Read 不存在的文件应报错。"""
    tool = ReadTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("no_such_file.txt")
    assert "文件不存在" in str(exc.value)


@pytest.mark.asyncio
async def test_read_rejects_path_traversal(file_tools, workspace):
    """Read 路径穿越应报错。"""
    tool = ReadTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("../../etc/passwd")
    assert "穿越" in str(exc.value)


@pytest.mark.asyncio
async def test_read_view_range_end_minus_one(file_tools, workspace):
    """Read view_range end=-1 表示到文件末尾。"""
    Path(workspace.root, "lines.txt").write_text(
        "line1\nline2\nline3\nline4\nline5\n", encoding="utf-8"
    )
    tool = ReadTool(file_tools=file_tools)
    result = await tool._arun("lines.txt", view_range=[3, -1])
    lines = result.strip().split("\n")
    assert lines == ["line3", "line4", "line5"]


# --- Write 边界 ---

@pytest.mark.asyncio
async def test_write_creates_subdirectory(file_tools, workspace):
    """Write 子目录不存在时应自动创建。"""
    tool = WriteTool(file_tools=file_tools)
    result = await tool._arun("sub/dir/new.txt", "nested content")
    assert "写入成功" in result
    content = Path(workspace.root, "sub", "dir", "new.txt").read_text(encoding="utf-8")
    assert content == "nested content"


@pytest.mark.asyncio
async def test_write_rejects_path_traversal(file_tools, workspace):
    """Write 路径穿越应报错。"""
    tool = WriteTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("../../evil.txt", "bad content")
    assert "穿越" in str(exc.value)


# --- Edit 边界 ---

@pytest.mark.asyncio
async def test_edit_nonexistent_file(file_tools, workspace):
    """Edit 不存在的文件应报错。"""
    tool = EditTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("no_such.txt", "old", "new")
    assert "文件不存在" in str(exc.value)


@pytest.mark.asyncio
async def test_edit_rejects_path_traversal(file_tools, workspace):
    """Edit 路径穿越应报错。"""
    tool = EditTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("../../evil.txt", "old", "new")
    assert "穿越" in str(exc.value)


@pytest.mark.asyncio
async def test_edit_only_replaces_first_occurrence(file_tools, workspace):
    """Edit 只替换第一次出现。"""
    Path(workspace.root, "test.txt").write_text("aaa bbb aaa", encoding="utf-8")
    tool = EditTool(file_tools=file_tools)
    result = await tool._arun("test.txt", "aaa", "ccc")
    assert "修改成功" in result
    content = Path(workspace.root, "test.txt").read_text(encoding="utf-8")
    assert content == "ccc bbb aaa"


# --- Insert 边界 ---

@pytest.mark.asyncio
async def test_insert_nonexistent_file(file_tools, workspace):
    """Insert 不存在的文件应报错。"""
    tool = InsertTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("no_such.txt", 0, "text")
    assert "文件不存在" in str(exc.value)


@pytest.mark.asyncio
async def test_insert_negative_line(file_tools, workspace):
    """Insert 负数行号应报错。"""
    Path(workspace.root, "test.txt").write_text("line1\n", encoding="utf-8")
    tool = InsertTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("test.txt", -1, "bad")
    assert "超出" in str(exc.value)


@pytest.mark.asyncio
async def test_insert_at_last_line(file_tools, workspace):
    """Insert 在最后一行后插入。"""
    Path(workspace.root, "test.txt").write_text("line1\nline2\n", encoding="utf-8")
    tool = InsertTool(file_tools=file_tools)
    result = await tool._arun("test.txt", 2, "appended")
    assert "插入成功" in result
    content = Path(workspace.root, "test.txt").read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert lines[-1] == "appended"


# --- Glob 边界 ---

@pytest.mark.asyncio
async def test_glob_nonexistent_path(file_tools, workspace):
    """Glob 不存在的路径应报错。"""
    tool = GlobTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("*.txt", path="no_such_dir")
    assert "不是目录" in str(exc.value)


@pytest.mark.asyncio
async def test_glob_results_sorted_by_mtime(file_tools, workspace):
    """Glob 结果按修改时间倒序排列。"""
    import time

    Path(workspace.root, "old.txt").write_text("old", encoding="utf-8")
    time.sleep(0.05)
    Path(workspace.root, "new.txt").write_text("new", encoding="utf-8")

    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("*.txt")
    lines = result.strip().split("\n")
    assert lines[0] == "new.txt"
    assert lines[1] == "old.txt"


@pytest.mark.asyncio
async def test_glob_multiple_skip_dirs(file_tools, workspace):
    """Glob 跳过多个忽略目录。"""
    for d in [".git", "node_modules", "__pycache__", "dist"]:
        Path(workspace.root, d).mkdir()
        Path(workspace.root, d, "secret.py").write_text("secret", encoding="utf-8")
    Path(workspace.root, "app.py").write_text("app", encoding="utf-8")

    tool = GlobTool(file_tools=file_tools)
    result = await tool._arun("**/*.py")
    assert "app.py" in result
    assert ".git" not in result
    assert "node_modules" not in result
    assert "__pycache__" not in result
    assert "dist" not in result


# --- Grep 边界 ---

@pytest.mark.asyncio
async def test_grep_nonexistent_path(file_tools, workspace):
    """Grep 不存在的路径应报错。"""
    tool = GrepTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("pattern", path="no_such_dir")
    assert "不是目录" in str(exc.value)


@pytest.mark.asyncio
async def test_grep_include_brace_expansion(file_tools, workspace):
    """Grep include 支持 {ts,tsx} 大括号展开。"""
    Path(workspace.root, "app.ts").write_text("const x = 1\n", encoding="utf-8")
    Path(workspace.root, "comp.tsx").write_text("const y = 2\n", encoding="utf-8")
    Path(workspace.root, "style.css").write_text("const z = 3\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("const", include="*.{ts,tsx}")
    assert "app.ts" in result
    assert "comp.tsx" in result
    assert "style.css" not in result


@pytest.mark.asyncio
async def test_grep_truncates_long_lines(file_tools, workspace):
    """Grep 匹配行超过 200 字符应截断。"""
    long_line = "x" * 300
    Path(workspace.root, "long.py").write_text(f"{long_line}\n", encoding="utf-8")

    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("x{300}")
    assert "..." in result  # 截断标记
    # 单行结果不应包含完整 300 字符
    result_line = [l for l in result.split("\n") if "long.py" in l][0]
    assert len(result_line) < 350


@pytest.mark.asyncio
async def test_grep_multi_line_matches_in_same_file(file_tools, workspace):
    """Grep 同一文件多行匹配都应返回。"""
    Path(workspace.root, "multi.py").write_text(
        "def foo():\n    pass\n\ndef bar():\n    pass\n", encoding="utf-8"
    )
    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun("def ")
    lines = [l for l in result.split("\n") if l.strip() and "multi.py" in l]
    assert len(lines) == 2


@pytest.mark.asyncio
async def test_grep_regex_pattern(file_tools, workspace):
    """Grep 支持正则表达式。"""
    Path(workspace.root, "test.py").write_text(
        "import os\nimport sys\nfrom os import path\n", encoding="utf-8"
    )
    tool = GrepTool(file_tools=file_tools)
    result = await tool._arun(r"import\s+\w+")
    assert "import os" in result
    assert "import sys" in result


@pytest.mark.asyncio
async def test_grep_invalid_regex(file_tools, workspace):
    """Grep 无效正则应报错。"""
    tool = GrepTool(file_tools=file_tools)
    with pytest.raises(Exception) as exc:
        await tool._arun("[invalid")
    assert "正则表达式无效" in str(exc.value)


# --- 跨工具边界 ---

@pytest.mark.asyncio
async def test_write_then_read_roundtrip(file_tools, workspace):
    """Write 写入后 Read 应能读到相同内容。"""
    content = "你好世界\nsecond line\n"
    write_tool = WriteTool(file_tools=file_tools)
    await write_tool._arun("roundtrip.txt", content)

    read_tool = ReadTool(file_tools=file_tools)
    result = await read_tool._arun("roundtrip.txt")
    assert result == content


@pytest.mark.asyncio
async def test_write_then_grep_finds_content(file_tools, workspace):
    """Write 写入后 Grep 应能搜到内容。"""
    write_tool = WriteTool(file_tools=file_tools)
    await write_tool._arun("searchable.py", "find_me_function()\n")

    grep_tool = GrepTool(file_tools=file_tools)
    result = await grep_tool._arun("find_me")
    assert "searchable.py" in result


@pytest.mark.asyncio
async def test_glob_then_read_roundtrip(file_tools, workspace):
    """Glob 找到文件后 Read 应能读取。"""
    Path(workspace.root, "target.vue").write_text("<template>hello</template>", encoding="utf-8")

    glob_tool = GlobTool(file_tools=file_tools)
    glob_result = await glob_tool._arun("*.vue")
    assert "target.vue" in glob_result

    read_tool = ReadTool(file_tools=file_tools)
    content = await read_tool._arun("target.vue")
    assert "<template>hello</template>" in content
