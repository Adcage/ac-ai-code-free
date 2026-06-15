import pytest

from app.grpc import common_pb2


class TestRouteCodeGenType:
    @pytest.mark.asyncio
    async def test_vue_project_keywords(self):
        from app.grpc_server.code_generation_servicer import CodeGenerationServicer

        servicer = CodeGenerationServicer()
        from unittest.mock import MagicMock

        request = MagicMock()
        request.prompt = "帮我生成一个Vue后台管理系统"
        result = await servicer.RouteCodeGenType(request, None)
        assert result.code_gen_type == common_pb2.VUE_PROJECT

    @pytest.mark.asyncio
    async def test_multi_file_keywords(self):
        from app.grpc_server.code_generation_servicer import CodeGenerationServicer

        servicer = CodeGenerationServicer()
        from unittest.mock import MagicMock

        request = MagicMock()
        request.prompt = "生成多个文件的CSS和JS"
        result = await servicer.RouteCodeGenType(request, None)
        assert result.code_gen_type == common_pb2.MULTI_FILE

    @pytest.mark.asyncio
    async def test_single_file_default(self):
        from app.grpc_server.code_generation_servicer import CodeGenerationServicer

        servicer = CodeGenerationServicer()
        from unittest.mock import MagicMock

        request = MagicMock()
        request.prompt = "生成一个简单的计算器"
        result = await servicer.RouteCodeGenType(request, None)
        assert result.code_gen_type == common_pb2.SINGLE_FILE
