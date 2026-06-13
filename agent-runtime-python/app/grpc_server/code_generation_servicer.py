import grpc
import logging

from app.grpc import code_generation_pb2
from app.grpc import code_generation_pb2_grpc
from app.grpc import common_pb2
from app.grpc_client.platform_client import GrpcPlatformClient
from app.schemas.code_generation import CodeGenerationRequest as PyCodeGenRequest
from app.services.chat_model_factory import ChatModelFactory
from app.services.prompt_enhancer import PromptEnhancerService

logger = logging.getLogger("app.grpc_server.code_generation_servicer")


def _map_event_type(event_type: str) -> int:
    mapping = {
        "agent_start": common_pb2.AGENT_START,
        "ai_response": common_pb2.AI_RESPONSE,
        "tool_request": common_pb2.TOOL_REQUEST,
        "tool_executed": common_pb2.TOOL_EXECUTED,
        "error": common_pb2.ERROR,
        "done": common_pb2.DONE,
    }
    return mapping.get(event_type, common_pb2.EVENT_TYPE_UNSPECIFIED)


def _map_code_gen_type(code_gen_type: str) -> int:
    mapping = {
        "single_file": common_pb2.SINGLE_FILE,
        "multi-file": common_pb2.MULTI_FILE,
        "vue_project": common_pb2.VUE_PROJECT,
    }
    return mapping.get(code_gen_type, common_pb2.VUE_PROJECT)


def _build_grpc_event(event) -> code_generation_pb2.CodeGenerationEvent:
    builder = code_generation_pb2.CodeGenerationEvent(
        agent_run_id=event.agentRunId,
        seq=event.seq,
        event_type=_map_event_type(event.eventType),
    )
    data = event.data

    if event.eventType == "ai_response":
        text = data.get("text", data.get("content", ""))
        builder.ai_response.CopyFrom(common_pb2.AiResponseData(
            text=text,
            fallback=data.get("fallback", False),
        ))
    elif event.eventType == "tool_request":
        arguments = data.get("arguments", "{}")
        if not isinstance(arguments, str):
            arguments = str(arguments)
        builder.tool_request.CopyFrom(common_pb2.ToolRequestData(
            id=data.get("id", "unknown"),
            name=data.get("name", "unknown"),
            arguments=arguments,
        ))
    elif event.eventType == "tool_executed":
        arguments = data.get("arguments", "{}")
        if not isinstance(arguments, str):
            arguments = str(arguments)
        builder.tool_executed.CopyFrom(common_pb2.ToolExecutedData(
            id=data.get("id", "unknown"),
            name=data.get("name", "unknown"),
            arguments=arguments,
            result=data.get("result", ""),
        ))
    elif event.eventType == "error":
        builder.error.CopyFrom(common_pb2.ErrorData(
            message=data.get("message", "unknown error"),
        ))
    elif event.eventType == "done":
        builder.done.CopyFrom(common_pb2.DoneData(
            message=data.get("message", ""),
        ))
    elif event.eventType == "agent_start":
        builder.ai_response.CopyFrom(common_pb2.AiResponseData(
            text="Agent started",
        ))

    return builder


class CodeGenerationServicer(code_generation_pb2_grpc.CodeGenerationServiceServicer):

    def __init__(self, agent_service):
        self._agent_service = agent_service

    async def StreamGenerate(self, request, context):
        py_request = PyCodeGenRequest(
            agentRunId=request.agent_run_id,
            appId=request.app_id,
            sessionId=request.session_id,
            userId=request.user_id,
            prompt=request.prompt,
            codeGenType=_grpc_code_gen_type_to_str(request.code_gen_type),
            workspacePath=request.workspace_path or None,
            modelConfigId=request.model_config_id or None,
            configVersion=request.config_version or None,
        )
        try:
            async for event in self._agent_service.stream(py_request):
                grpc_event = _build_grpc_event(event)
                yield grpc_event
        except Exception as e:
            logger.error("StreamGenerate failed: %s", e, exc_info=True)
            yield code_generation_pb2.CodeGenerationEvent(
                agent_run_id=request.agent_run_id,
                seq=0,
                event_type=common_pb2.ERROR,
                error=common_pb2.ErrorData(message=str(e)),
            )

    async def StreamModify(self, request, context):
        py_request = PyCodeGenRequest(
            agentRunId=request.agent_run_id,
            appId=request.app_id,
            sessionId=request.session_id,
            userId=request.user_id,
            prompt=request.prompt,
            codeGenType=_grpc_code_gen_type_to_str(request.code_gen_type),
            workspacePath=request.workspace_path or None,
            modelConfigId=request.model_config_id or None,
            configVersion=request.config_version or None,
        )
        try:
            async for event in self._agent_service.stream(py_request):
                grpc_event = _build_grpc_event(event)
                yield grpc_event
        except Exception as e:
            logger.error("StreamModify failed: %s", e, exc_info=True)
            yield code_generation_pb2.CodeGenerationEvent(
                agent_run_id=request.agent_run_id,
                seq=0,
                event_type=common_pb2.ERROR,
                error=common_pb2.ErrorData(message=str(e)),
            )

    async def RouteCodeGenType(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "RouteCodeGenType not yet implemented")

    async def ValidatePrompt(self, request, context):
        prompt = request.prompt
        if not prompt or len(prompt.strip()) == 0:
            return code_generation_pb2.ValidatePromptResponse(valid=False, reason="提示词不能为空")
        if len(prompt) > 2000:
            return code_generation_pb2.ValidatePromptResponse(valid=False, reason="提示词长度不能超过2000字")
        injection_keywords = ["ignore previous instructions", "bypass", "jailbreak"]
        lower = prompt.lower()
        for kw in injection_keywords:
            if kw in lower:
                return code_generation_pb2.ValidatePromptResponse(valid=False, reason="提示词包含不允许的内容")
        return code_generation_pb2.ValidatePromptResponse(valid=True)

    async def EnhancePrompt(self, request, context):
        prompt = request.prompt
        model_config_id = request.model_config_id
        config_version = request.config_version

        if not prompt or not prompt.strip():
            return code_generation_pb2.EnhancePromptResponse(
                success=False, error_message="提示词不能为空"
            )

        try:
            platform_client = GrpcPlatformClient()
            model_config = await platform_client.get_model_config(model_config_id, config_version)
            chat_model_factory = ChatModelFactory()
            enhancer = PromptEnhancerService(chat_model_factory)
            enhanced = await enhancer.enhance(prompt, model_config)
            return code_generation_pb2.EnhancePromptResponse(success=True, enhanced_prompt=enhanced)
        except Exception as e:
            logger.error("EnhancePrompt failed: %s", e, exc_info=True)
            return code_generation_pb2.EnhancePromptResponse(
                success=False, error_message=str(e)
            )


def _grpc_code_gen_type_to_str(code_gen_type_value: int) -> str:
    mapping = {
        common_pb2.SINGLE_FILE: "single_file",
        common_pb2.MULTI_FILE: "multi-file",
        common_pb2.VUE_PROJECT: "vue_project",
    }
    return mapping.get(code_gen_type_value, "vue_project")
