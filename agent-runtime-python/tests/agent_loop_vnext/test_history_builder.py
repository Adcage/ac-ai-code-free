"""测试 HistoryBuilder 多模态消息构建。"""

from unittest.mock import AsyncMock, patch

import pytest

from app.agent_loop_vnext.shared.history import HistoryBuilder
from app.runtime.context import AttachmentInfo, ChatHistoryEntry, ExecutionContext, CodeGenType, RunMode


@pytest.fixture
def builder():
    return HistoryBuilder()


@pytest.fixture
def base_context():
    return ExecutionContext(
        agent_run_id=1,
        app_id=100,
        session_id=200,
        user_id=1,
        prompt="",
        code_gen_type=CodeGenType.SINGLE_FILE,
        workspace_path="/tmp/ws",
        run_mode=RunMode.GENERATE,
    )


def _make_att(**kwargs) -> AttachmentInfo:
    """创建 AttachmentInfo 实例。"""
    defaults = dict(
        id="att-1",
        file_name="test.png",
        file_size=1024,
        mime_type="image/png",
        storage_type="local",
        storage_path="chat_attachments/2026/06/27/test.png",
        url="http://localhost:8700/api/file/chat-attachment/chat_attachments/2026/06/27/test.png",
    )
    defaults.update(kwargs)
    return AttachmentInfo(**defaults)


# ==================== 纯文本（向后兼容） ====================

class TestTextOnly:
    @pytest.mark.asyncio
    async def test_text_only_message(self, builder):
        """没有附件时，HumanMessage 应只包含文本。"""
        msg = await builder._build_user_message("Hello", ())
        content = msg.content
        if isinstance(content, list):
            assert len(content) == 1
            assert content[0]["type"] == "text"
            assert content[0]["text"] == "Hello"
        else:
            assert content == "Hello"

    @pytest.mark.asyncio
    async def test_empty_prompt_and_no_attachments(self, builder):
        """没有文本和附件时，应返回空 HumanMessage。"""
        msg = await builder._build_user_message("", ())
        assert msg is not None

    @pytest.mark.asyncio
    async def test_user_history_no_attachments(self, builder):
        """只有文本的历史用户条目应构造为普通 HumanMessage。"""
        entry = ChatHistoryEntry(id=1, role="user", content="历史问题")
        msg = await builder._message_from_role(entry.role, entry.content, entry.attachments)
        assert msg.content == "历史问题"

    @pytest.mark.asyncio
    async def test_ai_message_ignores_attachments(self, builder):
        """AI 消息即使有附件也不处理（AI 不会发送附件）。"""
        att = _make_att()
        entry = ChatHistoryEntry(id=1, role="ai", content="AI 回复", attachments=(att,))
        msg = await builder._message_from_role(entry.role, entry.content, entry.attachments)
        assert msg.content == "AI 回复"

    @pytest.mark.asyncio
    async def test_build_messages_no_attachments(self, builder, base_context):
        """build_messages 在不含附件时应保持向后兼容。"""
        context = ExecutionContext(**{**base_context.__dict__, "prompt": "用户消息"})
        messages = await builder.build_messages(context, "system prompt")
        assert len(messages) >= 2  # system + user
        assert messages[0].content == "system prompt"
        # 最后一条消息应包含用户消息
        last_msg = messages[-1]
        assert "用户消息" in str(last_msg.content)

    @pytest.mark.asyncio
    async def test_duplicate_history_dedup(self, builder):
        """最后一条历史与当前 prompt 重复时应去重。"""
        entry = ChatHistoryEntry(id=1, role="user", content="重复消息")
        context = ExecutionContext(
            agent_run_id=1, app_id=1, session_id=1, user_id=1,
            prompt="重复消息",
            code_gen_type=CodeGenType.SINGLE_FILE,
            workspace_path="/tmp/ws", run_mode=RunMode.GENERATE,
            chat_history=(entry,),
        )
        messages = await builder.build_messages(context, "prompt")
        # 不应有两条重复的用户消息
        user_msgs = [m for m in messages if hasattr(m, 'content') and str(m.content) == "重复消息"]
        assert len(user_msgs) == 0  # 被去重了


# ==================== 图片附件 ====================

class TestImageAttachments:
    @pytest.mark.asyncio
    async def test_image_local_storage(self, builder):
        """本地存储的图片应通过 httpx 拉取并转为 Base64 data URL。"""
        att = _make_att(storage_type="local")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"fake-image-bytes"
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await builder._resolve_image(att)
            assert result is not None
            assert result["type"] == "image_url"
            assert result["image_url"]["url"].startswith("data:image/png;base64,")
            mock_instance.get.assert_called_once_with(att.url)

    @pytest.mark.asyncio
    async def test_image_cos_storage(self, builder):
        """COS 存储的图片应直接使用公网 URL。"""
        att = _make_att(storage_type="cos", url="https://cdn.example.com/test.png")

        result = await builder._resolve_image(att)
        assert result is not None
        assert result["type"] == "image_url"
        assert result["image_url"]["url"] == "https://cdn.example.com/test.png"

    @pytest.mark.asyncio
    async def test_image_fetch_failure(self, builder):
        """图片拉取失败时应返回 None 并静默跳过。"""
        att = _make_att(storage_type="local")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await builder._resolve_image(att)
            assert result is None

    @pytest.mark.asyncio
    async def test_image_http_exception(self, builder):
        """HTTPS 请求异常时应返回 None。"""
        att = _make_att(storage_type="local")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = Exception("Connection refused")
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await builder._resolve_image(att)
            assert result is None


# ==================== 文档附件 ====================

class TestDocumentAttachments:
    @pytest.mark.asyncio
    async def test_text_file_attachment(self, builder):
        """文本文件应提取内容并追加为 text content block。"""
        att = _make_att(mime_type="text/plain", file_name="notes.txt", storage_type="local")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"Hello from file"
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await builder._resolve_document(att)
            assert result is not None
            assert "notes.txt" in result
            assert "Hello from file" in result

    @pytest.mark.asyncio
    async def test_document_fetch_failure(self, builder):
        """文档拉取失败应返回加载失败占位。"""
        att = _make_att(mime_type="text/plain", file_name="notes.txt")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await builder._resolve_document(att)
            assert result is not None
            assert "加载失败" in result

    @pytest.mark.asyncio
    async def test_document_cos_storage(self, builder):
        """COS 存储的文档直接从 URL 下载。"""
        att = _make_att(
            mime_type="text/plain", file_name="readme.txt",
            storage_type="cos", url="https://cdn.example.com/readme.txt",
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"COS file content"
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await builder._resolve_document(att)
            assert result is not None
            assert "COS file content" in result


# ==================== 多附件混合 ====================

class TestMixedAttachments:
    @pytest.mark.asyncio
    async def test_text_and_image_mixed(self, builder):
        """文本 + 图片应构造为混合 content parts。"""
        text_att = _make_att(id="1", mime_type="text/plain", file_name="readme.txt")
        img_att = _make_att(id="2", mime_type="image/png", file_name="screenshot.png",
                            storage_type="cos", url="https://cdn.example.com/screenshot.png")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"Text content"
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            msg = await builder._build_user_message("User query", (text_att, img_att))
            content = msg.content
            assert isinstance(content, list)
            assert len(content) == 3  # text + doc_text + image_url
            assert content[0]["type"] == "text"
            assert content[0]["text"] == "User query"
            assert content[2]["type"] == "image_url"

    @pytest.mark.asyncio
    async def test_all_images_no_text(self, builder):
        """只有图片没有文本时，content parts 应只包含图片。"""
        img1 = _make_att(id="1", storage_type="cos", url="https://cdn.example.com/1.png")
        img2 = _make_att(id="2", storage_type="cos", url="https://cdn.example.com/2.png")

        msg = await builder._build_user_message("", (img1, img2))
        content = msg.content
        assert isinstance(content, list)
        assert len(content) == 2
        assert all(c["type"] == "image_url" for c in content)

    @pytest.mark.asyncio
    async def test_all_failed_attachments(self, builder):
        """所有附件处理失败时，应添加错误占位文本而非崩溃。"""
        att = _make_att(mime_type="text/plain", file_name="fail.txt")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = Exception("Network error")
            mock_client.return_value.__aenter__.return_value = mock_instance

            msg = await builder._build_user_message("Fallback text", (att,))
            content = msg.content
            assert isinstance(content, list)
            # 用户文本 + 错误占位
            assert len(content) == 2
            assert content[0]["type"] == "text"
            assert "Fallback text" in content[0]["text"]
            assert content[1]["type"] == "text"
            # 包含加载失败提示
            assert "加载失败" in content[1]["text"] or "fail.txt" in content[1]["text"]


# ==================== 总文本上限 ====================

class TestTextLimit:
    @pytest.mark.asyncio
    async def test_total_text_truncation(self, builder):
        """多文档附件总文本超出 100000 字符时应截断。"""
        atts = [_make_att(id=str(i), mime_type="text/plain", file_name=f"doc{i}.txt")
                for i in range(3)]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"X" * 50_000
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            msg = await builder._build_user_message("Query", tuple(atts))
            content = msg.content
            assert isinstance(content, list)
            text_parts = [c for c in content if c["type"] == "text"]
            assert len(text_parts) >= 1  # 至少有 1 个文档的内容
            total_text_len = sum(len(c["text"]) for c in text_parts)
            assert total_text_len <= 110_000  # 接近限制

    @pytest.mark.asyncio
    async def test_small_documents_not_truncated(self, builder):
        """小文档不应被截断。"""
        att = _make_att(mime_type="text/plain", file_name="small.txt")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"Small content"
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            msg = await builder._build_user_message("Query", (att,))
            part = msg.content[1] if isinstance(msg.content, list) and len(msg.content) > 1 else msg.content[0]
            assert "截断" not in str(part.get("text", ""))
