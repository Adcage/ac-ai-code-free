import grpc
import pytest

from app.grpc import code_generation_pb2
from app.grpc_server.code_generation_servicer import CodeGenerationServicer


class FakeContext:
    def __init__(self):
        self.code = None
        self.details = None
        self.abort_code = None
        self.abort_details = None

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details

    async def abort(self, code, details):
        self.abort_code = code
        self.abort_details = details
        raise RuntimeError("aborted")


@pytest.mark.asyncio
async def test_route_code_gen_type_aborts_as_unimplemented():
    context = FakeContext()
    servicer = CodeGenerationServicer(agent_service=None)

    with pytest.raises(RuntimeError, match="aborted"):
        await servicer.RouteCodeGenType(code_generation_pb2.RouteCodeGenTypeRequest(prompt="test"), context)

    assert context.abort_code == grpc.StatusCode.UNIMPLEMENTED
    assert context.abort_details == "RouteCodeGenType not yet implemented"
