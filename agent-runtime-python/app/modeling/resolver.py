import logging
from dataclasses import dataclass

from app.modeling.roles import ModelRole

logger = logging.getLogger("app.modeling.resolver")


@dataclass(frozen=True)
class ResolvedModelConfig:
    role: ModelRole
    provider: str
    model_name: str
    base_url: str
    api_key: str
    source: str = ""
    billing_mode: str = ""


class ModelResolver:
    def __init__(self, platform_client) -> None:
        self._platform_client = platform_client
        self._bundle: dict[ModelRole, ResolvedModelConfig] = {}

    async def load_bundle(self, context) -> None:
        if self._bundle:
            return
        bundle = await self._platform_client.resolve_runtime_model_bundle(
            user_id=context.user_id,
            app_id=context.app_id,
            agent_run_id=context.agent_run_id,
            code_gen_type=context.code_gen_type.value,
        )
        self._bundle = bundle
        logger.info("model bundle loaded | roles=%s", list(self._bundle.keys()))

    def resolve(self, role: ModelRole) -> ResolvedModelConfig:
        if role in self._bundle:
            return self._bundle[role]
        if ModelRole.PRIMARY in self._bundle:
            return self._bundle[ModelRole.PRIMARY]
        raise RuntimeError("No runtime model config resolved")
