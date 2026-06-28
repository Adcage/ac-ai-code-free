import logging

from app.grpc import platform_service_pb2
from app.grpc import platform_service_pb2_grpc
from app.grpc import common_pb2
from app.grpc_client.channel import get_channel, get_internal_metadata
from app.grpc_client.retry import retry_async
from app.modeling.roles import ModelRole
from app.modeling.resolver import ResolvedModelConfig

logger = logging.getLogger("app.grpc_client.platform_client")


class GrpcPlatformClient:
    def __init__(self):
        self._stub: platform_service_pb2_grpc.PlatformServiceStub | None = None

    async def _get_stub(self) -> platform_service_pb2_grpc.PlatformServiceStub:
        if self._stub is None:
            channel = await get_channel()
            self._stub = platform_service_pb2_grpc.PlatformServiceStub(channel)
        return self._stub

    async def get_model_config(self, model_config_id: int, config_version: int) -> dict:
        async def _call():
            stub = await self._get_stub()
            request = platform_service_pb2.GetModelConfigRequest(
                model_config_id=model_config_id,
                config_version=config_version,
            )
            response = await stub.GetModelConfig(request, metadata=get_internal_metadata())
            return {
                "provider": response.provider,
                "modelName": response.model_name,
                "baseUrl": response.base_url,
                "apiKey": response.api_key,
            }

        return await retry_async(
            _call,
            max_retries=2,
            delay_seconds=1.0,
            label=f"get_model_config(id={model_config_id}, version={config_version})",
        )

    async def build_vue_project(self, app_id: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.BuildVueProjectRequest(app_id=app_id)
        response = await stub.BuildVueProject(request, metadata=get_internal_metadata())
        return {
            "success": response.success,
            "distPath": response.dist_path,
            "installLog": response.install_log,
            "buildLog": response.build_log,
            "errorMessage": response.error_message,
        }

    async def deploy_app(self, app_id: int, user_id: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.DeployAppRequest(app_id=app_id, user_id=user_id)
        response = await stub.DeployApp(request, metadata=get_internal_metadata())
        return {"success": response.success, "url": response.url, "errorMessage": response.error_message}

    async def complete_agent_run(
        self,
        agent_run_id: int,
        success: bool,
        workspace_path: str = "",
        latency_ms: int = 0,
        error_message: str = "",
        loop_state_json: str = "",
    ) -> bool:
        stub = await self._get_stub()
        request = platform_service_pb2.CompleteAgentRunRequest(
            agent_run_id=agent_run_id,
            success=success,
            workspace_path=workspace_path,
            latency_ms=latency_ms,
            error_message=error_message,
            loop_state_json=loop_state_json,
        )
        response = await stub.CompleteAgentRun(request, metadata=get_internal_metadata())
        return response.ok

    async def create_app_version(
        self, app_id: int, agent_run_id: int, source_path: str, build_path: str
    ) -> int:
        stub = await self._get_stub()
        request = platform_service_pb2.CreateAppVersionRequest(
            app_id=app_id,
            agent_run_id=agent_run_id,
            source_path=source_path,
            build_path=build_path,
        )
        response = await stub.CreateAppVersion(request, metadata=get_internal_metadata())
        return response.version_id

    async def get_chat_history(self, session_id: int, limit: int = 50) -> list[dict]:
        stub = await self._get_stub()
        request = platform_service_pb2.GetChatHistoryRequest(session_id=session_id, limit=limit)
        response = await stub.GetChatHistory(request, metadata=get_internal_metadata())
        return [{"id": e.id, "role": e.role, "content": e.content, "attachments_json": e.attachments_json} for e in response.entries]

    async def get_app_detail(self, app_id: int) -> dict:
        stub = await self._get_stub()
        request = platform_service_pb2.GetAppDetailRequest(app_id=app_id)
        response = await stub.GetAppDetail(request, metadata=get_internal_metadata())
        return {
            "id": response.id,
            "name": response.name,
            "description": response.description,
            "codeGenType": response.code_gen_type,
            "userId": response.user_id,
        }

    async def resolve_runtime_model_bundle(
        self,
        user_id: int,
        app_id: int,
        agent_run_id: int,
        code_gen_type: str,
    ) -> dict[ModelRole, ResolvedModelConfig]:
        stub = await self._get_stub()
        code_gen_type_proto = _map_code_gen_type(code_gen_type)
        request = platform_service_pb2.ResolveRuntimeModelBundleRequest(
            user_id=user_id,
            app_id=app_id,
            agent_run_id=agent_run_id,
            code_gen_type=code_gen_type_proto,
        )
        response = await stub.ResolveRuntimeModelBundle(request, metadata=get_internal_metadata())

        if not response.success:
            raise RuntimeError(f"resolve_runtime_model_bundle failed: {response.error_message}")

        bundle: dict[ModelRole, ResolvedModelConfig] = {}
        for config in response.configs:
            role = ModelRole(config.role)
            bundle[role] = ResolvedModelConfig(
                role=role,
                provider=config.provider,
                model_name=config.model_name,
                base_url=config.base_url,
                api_key=config.api_key,
                model_config_id=config.model_config_id,
                config_version=config.config_version,
                source=config.source,
                billing_mode=config.billing_mode,
            )
        return bundle


def _map_code_gen_type(code_gen_type: str) -> int:
    mapping = {
        "single_file": common_pb2.SINGLE_FILE,
        "multi-file": common_pb2.MULTI_FILE,
        "vue_project": common_pb2.VUE_PROJECT,
    }
    return mapping.get(code_gen_type, common_pb2.SINGLE_FILE)
