import logging

from app.core.error_codes import AgentErrorCode
from app.grpc import code_generation_pb2
from app.grpc import code_generation_pb2_grpc
from app.grpc import common_pb2
from app.grpc_client.platform_client import GrpcPlatformClient
from app.runtime.orchestrator import RuntimeOrchestrator
from app.services.chat_model_factory import ChatModelFactory
from app.services.prompt_enhancer import PromptEnhancerService

logger = logging.getLogger("app.grpc_server.code_generation_servicer")

_EN_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "ignore the above",
    "disregard previous",
    "disregard all",
    "bypass",
    "jailbreak",
    "system prompt",
    "you are now",
    "act as",
    "pretend you are",
    "roleplay as",
    "new instruction",
    "override instruction",
    "forget everything",
    "forget your instructions",
    "ignore your rules",
    "do anything now",
    "DAN mode",
]

_CN_INJECTION_PATTERNS = [
    "忽略之前的指令",
    "忽略所有指令",
    "忽略上述",
    "无视之前的",
    "绕过限制",
    "越狱",
    "系统提示词",
    "你现在是一个",
    "假装你是",
    "扮演",
    "新指令",
    "覆盖指令",
    "忘记一切",
    "忘记你的指令",
    "忽略你的规则",
    "不受限制",
]

_ENCODING_TRICKS = [
    "\u200b",
    "\u200c",
    "\u200d",
    "\ufeff",
    "\u00ad",
    "\\x",
    "\\u00",
    "\\nignore",
    "\\n.system",
]


def _detect_prompt_injection(prompt: str) -> str:
    normalized = prompt.lower()
    stripped = "".join(c for c in normalized if c.isalnum() or c.isspace())

    for pattern in _EN_INJECTION_PATTERNS:
        if pattern in normalized or pattern in stripped:
            return f"提示词包含不允许的内容"

    for pattern in _CN_INJECTION_PATTERNS:
        if pattern in prompt or pattern in stripped:
            return f"提示词包含不允许的内容"

    for trick in _ENCODING_TRICKS:
        if trick in prompt:
            return f"提示词包含不允许的字符"

    role_patterns = ["<|im_start|>", "<|system|>", "[system]", "### system", "=== system"]
    for rp in role_patterns:
        if rp in normalized:
            return f"提示词包含不允许的内容"

    return ""


class CodeGenerationServicer(code_generation_pb2_grpc.CodeGenerationServiceServicer):
    async def StreamGenerate(self, request, context):
        logger.info("StreamGenerate | agentRunId=%s appId=%s", request.agent_run_id, request.app_id)
        try:
            orchestrator = RuntimeOrchestrator()
            async for event in orchestrator.stream_generate(request):
                yield event
        except Exception as e:
            logger.error(
                "StreamGenerate error | agentRunId=%s error=%s",
                request.agent_run_id,
                e,
                exc_info=True,
            )
            yield code_generation_pb2.CodeGenerationEvent(
                agent_run_id=request.agent_run_id,
                seq=1,
                event_type=common_pb2.ERROR,
                error=common_pb2.ErrorData(message=str(e), code=AgentErrorCode.INTERNAL_ERROR),
            )

    async def StreamModify(self, request, context):
        logger.info("StreamModify | agentRunId=%s appId=%s", request.agent_run_id, request.app_id)
        try:
            orchestrator = RuntimeOrchestrator()
            async for event in orchestrator.stream_modify(request):
                yield event
        except Exception as e:
            logger.error(
                "StreamModify error | agentRunId=%s error=%s",
                request.agent_run_id,
                e,
                exc_info=True,
            )
            yield code_generation_pb2.CodeGenerationEvent(
                agent_run_id=request.agent_run_id,
                seq=1,
                event_type=common_pb2.ERROR,
                error=common_pb2.ErrorData(message=str(e), code=AgentErrorCode.INTERNAL_ERROR),
            )

    async def ValidatePrompt(self, request, context):
        prompt = request.prompt
        if not prompt or len(prompt.strip()) == 0:
            return code_generation_pb2.ValidatePromptResponse(
                valid=False, reason=f"[{AgentErrorCode.PROMPT_EMPTY}] 提示词不能为空"
            )
        if len(prompt) > 2000:
            return code_generation_pb2.ValidatePromptResponse(
                valid=False,
                reason=f"[{AgentErrorCode.PROMPT_LENGTH_EXCEEDED}] 提示词长度不能超过2000字",
            )
        injection_result = _detect_prompt_injection(prompt)
        if injection_result:
            return code_generation_pb2.ValidatePromptResponse(
                valid=False,
                reason=f"[{AgentErrorCode.PROMPT_INJECTION_DETECTED}] {injection_result}",
            )
        return code_generation_pb2.ValidatePromptResponse(valid=True)

    async def EnhancePrompt(self, request, context):
        prompt = request.prompt

        logger.info(
            "EnhancePrompt called, promptLength=%d",
            len(prompt) if prompt else 0,
        )

        if not prompt or not prompt.strip():
            return code_generation_pb2.EnhancePromptResponse(
                success=False, error_message=f"[{AgentErrorCode.PROMPT_EMPTY}] 提示词不能为空"
            )

        try:
            platform_client = GrpcPlatformClient()
            # 使用系统级模型配置解析 bundle
            bundle = await platform_client.resolve_runtime_model_bundle(
                user_id=0, app_id=0, agent_run_id=0, code_gen_type="single_file"
            )
            from app.modeling.roles import ModelRole
            resolved = bundle.get(ModelRole.PRIMARY) or bundle.get(ModelRole.LIGHT)
            if resolved is None:
                return code_generation_pb2.EnhancePromptResponse(
                    success=False, error_message="没有可用的模型配置"
                )
            model_config = {
                "provider": resolved.provider,
                "modelName": resolved.model_name,
                "baseUrl": resolved.base_url,
                "apiKey": resolved.api_key,
            }
            logger.info(
                "EnhancePrompt using system model, provider=%s, modelName=%s",
                resolved.provider,
                resolved.model_name,
            )
            chat_model_factory = ChatModelFactory()
            enhancer = PromptEnhancerService(chat_model_factory)
            enhanced = await enhancer.enhance(prompt, model_config)
            logger.info(
                "EnhancePrompt success, enhancedLength=%d", len(enhanced) if enhanced else 0
            )
            return code_generation_pb2.EnhancePromptResponse(success=True, enhanced_prompt=enhanced)
        except Exception as e:
            logger.error("EnhancePrompt failed: %s", e, exc_info=True)
            return code_generation_pb2.EnhancePromptResponse(success=False, error_message=str(e))
