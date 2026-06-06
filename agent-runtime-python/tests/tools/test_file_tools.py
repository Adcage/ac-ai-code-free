from pathlib import Path

import pytest

from app.core.exceptions import AgentRuntimeError
from app.tools.file_tools import FileTools
from app.tools.workspace import Workspace


def test_write_and_read_file(tmp_path: Path):
    tools = FileTools(Workspace(tmp_path))

    write_result = tools.write_file("src/App.vue", "<template>Hello</template>")
    content = tools.read_file("src/App.vue")

    assert write_result == "写入成功: src/App.vue"
    assert content == "<template>Hello</template>"


def test_modify_file_replaces_content(tmp_path: Path):
    tools = FileTools(Workspace(tmp_path))
    tools.write_file("src/App.vue", "hello world")

    result = tools.modify_file("src/App.vue", "world", "vue")

    assert result == "修改成功: src/App.vue"
    assert tools.read_file("src/App.vue") == "hello vue"


def test_modify_file_rejects_missing_target(tmp_path: Path):
    tools = FileTools(Workspace(tmp_path))
    tools.write_file("src/App.vue", "hello")

    with pytest.raises(AgentRuntimeError):
        tools.modify_file("src/App.vue", "missing", "vue")


def test_delete_protects_core_files(tmp_path: Path):
    tools = FileTools(Workspace(tmp_path))
    tools.write_file("package.json", "{}")

    with pytest.raises(AgentRuntimeError):
        tools.delete_file("package.json")


def test_read_dir_lists_relative_paths(tmp_path: Path):
    tools = FileTools(Workspace(tmp_path))
    tools.write_file("src/App.vue", "hello")
    tools.write_file("src/main.ts", "main")

    result = tools.read_dir("src")

    assert "App.vue" in result
    assert "main.ts" in result
