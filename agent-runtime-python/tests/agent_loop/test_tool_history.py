from app.agent_loop.tool_history import compact_tool_records
from app.runtime.state import ToolCallRecord


def test_write_file_content_is_not_replayed():
    records = [
        ToolCallRecord(
            id="w1",
            name="write_file",
            arguments={"relative_path": "src/App.vue", "content": "x" * 20_000},
            result="文件写入成功",
        )
    ]

    compacted = compact_tool_records(
        records,
        max_total_chars=10_000,
        max_result_chars=2_000,
    )

    assert "content" not in compacted[0].arguments
    assert compacted[0].arguments["content_length"] == 20_000
    assert compacted[0].arguments["relative_path"] == "src/App.vue"


def test_read_file_result_keeps_head_and_tail():
    result = "HEAD" + "x" * 20_000 + "TAIL"
    records = [
        ToolCallRecord(id="r1", name="read_file", arguments={}, result=result)
    ]

    compacted = compact_tool_records(
        records,
        max_total_chars=10_000,
        max_result_chars=1_000,
    )

    assert compacted[0].result.startswith("HEAD")
    assert compacted[0].result.endswith("TAIL")
    assert "已省略" in compacted[0].result
    assert len(compacted[0].result) <= 1_000


def test_total_budget_prefers_latest_tool_records():
    records = [
        ToolCallRecord(
            id=str(index),
            name="run_command",
            arguments={},
            result=str(index) * 2_000,
        )
        for index in range(5)
    ]

    compacted = compact_tool_records(
        records,
        max_total_chars=3_500,
        max_result_chars=2_000,
    )

    assert compacted[-1].id == "4"
    assert sum(len(record.result or "") for record in compacted) <= 3_500
