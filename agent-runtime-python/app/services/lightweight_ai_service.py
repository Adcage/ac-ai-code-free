import logging

from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError
from app.grpc_client.platform_client import GrpcPlatformClient
from app.modeling.roles import ModelRole
from app.services.chat_model_factory import ChatModelFactory
from app.services.prompt_enhancer import PromptEnhancerService
from app.services.title_generator import TitleGeneratorService

logger = logging.getLogger("app.services.lightweight_ai_service")


class LightweightAiService:
    def __init__(
        self,
        platform_client: GrpcPlatformClient | None = None,
        chat_model_factory: ChatModelFactory | None = None,
        prompt_enhancer: PromptEnhancerService | None = None,
        title_generator: TitleGeneratorService | None = None,
    ):
        self.platform_client = platform_client or GrpcPlatformClient()
        self.chat_model_factory = chat_model_factory or ChatModelFactory()
        self.prompt_enhancer = prompt_enhancer or PromptEnhancerService(self.chat_model_factory)
        self.title_generator = title_generator or TitleGeneratorService(self.chat_model_factory)

    async def enhance_prompt(self, prompt: str) -> str:
        model_config = await self._resolve_model_config()
        return await self.prompt_enhancer.enhance(prompt, model_config)

    async def generate_app_title(self, init_prompt: str) -> str:
        model_config = await self._resolve_model_config()
        return await self.title_generator.generate_app_title(init_prompt, model_config)

    async def generate_session_title(
        self, app_name: str, app_init_prompt: str, first_user_message: str
    ) -> str:
        model_config = await self._resolve_model_config()
        return await self.title_generator.generate_session_title(
            app_name, app_init_prompt, first_user_message, model_config
        )

    async def _resolve_model_config(self) -> dict:
        bundle = await self.platform_client.resolve_runtime_model_bundle(
            user_id=0, app_id=0, agent_run_id=0, code_gen_type="single_file"
        )
        resolved = bundle.get(ModelRole.LIGHT) or bundle.get(ModelRole.PRIMARY)
        if resolved is None:
            raise AgentRuntimeError("没有可用的轻量模型配置", code=AgentErrorCode.MODEL_CONFIG_MISSING)
        logger.info(
            "lightweight ai using model | role=%s provider=%s model=%s",
            resolved.role.value,
            resolved.provider,
            resolved.model_name,
        )
        return {
            "provider": resolved.provider,
            "modelName": resolved.model_name,
            "baseUrl": resolved.base_url,
            "apiKey": resolved.api_key,
        }
