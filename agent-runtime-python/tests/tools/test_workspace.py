from pathlib import Path

import pytest

from app.core.exceptions import AgentRuntimeError
from app.tools.workspace import Workspace


def test_resolve_allows_file_inside_workspace(tmp_path: Path):
    workspace = Workspace(tmp_path)

    resolved = workspace.resolve("src/App.vue")

    assert resolved == tmp_path / "src" / "App.vue"


def test_resolve_rejects_path_traversal(tmp_path: Path):
    workspace = Workspace(tmp_path)

    with pytest.raises(AgentRuntimeError):
        workspace.resolve("../secret.txt")


def test_resolve_rejects_absolute_path_outside_workspace(tmp_path: Path):
    workspace = Workspace(tmp_path)
    outside = tmp_path.parent / "secret.txt"

    with pytest.raises(AgentRuntimeError):
        workspace.resolve(str(outside))
