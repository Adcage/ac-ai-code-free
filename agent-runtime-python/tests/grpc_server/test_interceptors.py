
import grpc

from app.grpc_server.interceptors import _wrap_handler, _RpcMethodHandler


class TestRpcMethodHandler:
    def test_unary_unary_handler(self):
        async def handler(request, context):
            return "response"

        original = _RpcMethodHandler(
            unary_unary=handler,
            request_deserializer=None,
            response_serializer=None,
        )
        wrapped = _wrap_handler(original, unary_unary=handler)
        assert wrapped.unary_unary is handler
        assert wrapped.unary_stream is None
        assert wrapped.request_streaming is False
        assert wrapped.response_streaming is False

    def test_unary_stream_handler(self):
        async def handler(request, context):
            yield "event"

        original = _RpcMethodHandler(
            unary_stream=handler,
            request_deserializer=None,
            response_serializer=None,
        )
        wrapped = _wrap_handler(original, unary_stream=handler)
        assert wrapped.unary_stream is handler
        assert wrapped.unary_unary is None
        assert wrapped.request_streaming is False
        assert wrapped.response_streaming is True

    def test_preserves_deserializer_and_serializer(self):
        original = _RpcMethodHandler(
            unary_unary=lambda r, c: None,
            request_deserializer=lambda b: b,
            response_serializer=lambda o: o,
        )
        wrapped = _wrap_handler(original)
        assert wrapped.request_deserializer is original.request_deserializer
        assert wrapped.response_serializer is original.response_serializer

    def test_is_grpc_rpc_method_handler(self):
        handler = _RpcMethodHandler(unary_unary=lambda r, c: None)
        assert isinstance(handler, grpc.RpcMethodHandler)

    def test_all_required_attributes_present(self):
        handler = _RpcMethodHandler(unary_stream=lambda r, c: None)
        assert hasattr(handler, "request_streaming")
        assert hasattr(handler, "response_streaming")
        assert hasattr(handler, "request_deserializer")
        assert hasattr(handler, "response_serializer")
        assert hasattr(handler, "unary_unary")
        assert hasattr(handler, "unary_stream")
        assert hasattr(handler, "stream_unary")
        assert hasattr(handler, "stream_stream")
