import asyncio
import grpc
import sys

sys.path.insert(0, ".")

from app.grpc import platform_service_pb2, platform_service_pb2_grpc, common_pb2


async def test_platform_service():
    channel = grpc.aio.insecure_channel("localhost:9090")
    stub = platform_service_pb2_grpc.PlatformServiceStub(channel)
    results = []

    # 2.1 GetModelConfig
    try:
        resp = await stub.GetModelConfig(
            platform_service_pb2.GetModelConfigRequest(model_config_id=1, config_version=0)
        )
        base_url = resp.base_url[:30] if resp.base_url else "(none)"
        results.append(f"2.1 GetModelConfig: OK - provider={resp.provider}, model={resp.model_name}, baseUrl={base_url}")
    except Exception as e:
        results.append(f"2.1 GetModelConfig: FAIL - {e}")

    # 2.2 GetAppDetail
    try:
        resp = await stub.GetAppDetail(platform_service_pb2.GetAppDetailRequest(app_id=1))
        cgt = common_pb2.CodeGenType.Name(resp.code_gen_type)
        results.append(f"2.2 GetAppDetail: OK - id={resp.id}, name={resp.name}, codeGenType={cgt}")
    except Exception as e:
        results.append(f"2.2 GetAppDetail: FAIL - {e}")

    # 2.3 GetUserInfo
    try:
        resp = await stub.GetUserInfo(platform_service_pb2.GetUserInfoRequest(user_id=1))
        results.append(f"2.3 GetUserInfo: OK - id={resp.id}, name={resp.user_name}, role={resp.user_role}")
    except Exception as e:
        results.append(f"2.3 GetUserInfo: FAIL - {e}")

    # 2.4 GetChatHistory
    try:
        resp = await stub.GetChatHistory(platform_service_pb2.GetChatHistoryRequest(session_id=1, limit=10))
        results.append(f"2.4 GetChatHistory: OK - entries={len(resp.entries)}")
    except Exception as e:
        results.append(f"2.4 GetChatHistory: FAIL - {e}")

    # 2.5 CompleteAgentRun (success)
    try:
        resp = await stub.CompleteAgentRun(
            platform_service_pb2.CompleteAgentRunRequest(
                agent_run_id=1, success=True, workspace_path="/tmp/test", latency_ms=100
            )
        )
        results.append(f"2.5 CompleteAgentRun: OK - ok={resp.ok}")
    except Exception as e:
        results.append(f"2.5 CompleteAgentRun: FAIL - {e}")

    # 2.6 CompleteAgentRun (fail)
    try:
        resp = await stub.CompleteAgentRun(
            platform_service_pb2.CompleteAgentRunRequest(
                agent_run_id=999, success=False, error_message="test error"
            )
        )
        results.append(f"2.6 CompleteAgentRun(fail): OK - ok={resp.ok}")
    except Exception as e:
        results.append(f"2.6 CompleteAgentRun(fail): FAIL - {e}")

    # 2.7 UpdateAppCodeGenType
    try:
        resp = await stub.UpdateAppCodeGenType(
            platform_service_pb2.UpdateAppCodeGenTypeRequest(app_id=1, code_gen_type=common_pb2.VUE_PROJECT)
        )
        results.append(f"2.7 UpdateAppCodeGenType: OK - ok={resp.ok}")
    except Exception as e:
        results.append(f"2.7 UpdateAppCodeGenType: FAIL - {e}")

    # 2.8 BuildVueProject
    try:
        resp = await stub.BuildVueProject(platform_service_pb2.BuildVueProjectRequest(app_id=1))
        err = resp.error_message[:50] if resp.error_message else "(none)"
        results.append(f"2.8 BuildVueProject: OK - success={resp.success}, err={err}")
    except Exception as e:
        results.append(f"2.8 BuildVueProject: FAIL - {e}")

    # 2.9 CreateAppVersion
    try:
        resp = await stub.CreateAppVersion(
            platform_service_pb2.CreateAppVersionRequest(
                app_id=1, agent_run_id=1, source_path="/tmp/src", build_path="/tmp/dist"
            )
        )
        results.append(f"2.9 CreateAppVersion: OK - version_id={resp.version_id}")
    except Exception as e:
        results.append(f"2.9 CreateAppVersion: FAIL - {e}")

    await channel.close()
    return results


results = asyncio.run(test_platform_service())
for r in results:
    print(r)
if any("FAIL" in r for r in results):
    sys.exit(1)
