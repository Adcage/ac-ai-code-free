import asyncio
import grpc
import sys

sys.path.insert(0, ".")

from app.grpc import platform_service_pb2, platform_service_pb2_grpc, common_pb2


async def check():
    channel = grpc.aio.insecure_channel("localhost:9090")
    stub = platform_service_pb2_grpc.PlatformServiceStub(channel)

    for aid in [1, 2, 3, 4, 5, 10, 100]:
        try:
            resp = await stub.GetAppDetail(platform_service_pb2.GetAppDetailRequest(app_id=aid))
            cgt = common_pb2.CodeGenType.Name(resp.code_gen_type)
            print(f"app_id={aid}: id={resp.id}, name={resp.name}, codeGenType={cgt}, userId={resp.user_id}")
        except grpc.aio.AioRpcError as e:
            print(f"app_id={aid}: gRPC error - {e.code()}: {e.details()[:80]}")
        except Exception as e:
            print(f"app_id={aid}: FAIL - {e}")

    for uid in [1, 2, 3, 10, 100]:
        try:
            resp = await stub.GetUserInfo(platform_service_pb2.GetUserInfoRequest(user_id=uid))
            print(f"user_id={uid}: id={resp.id}, name={resp.user_name}, role={resp.user_role}")
        except grpc.aio.AioRpcError as e:
            print(f"user_id={uid}: gRPC error - {e.code()}: {e.details()[:80]}")
        except Exception as e:
            print(f"user_id={uid}: FAIL - {e}")

    # Check model configs
    for mid in [1, 2, 3]:
        try:
            resp = await stub.GetModelConfig(platform_service_pb2.GetModelConfigRequest(model_config_id=mid, config_version=0))
            print(f"model_config_id={mid}: provider={resp.provider}, model={resp.model_name}")
        except grpc.aio.AioRpcError as e:
            print(f"model_config_id={mid}: gRPC error - {e.code()}: {e.details()[:80]}")
        except Exception as e:
            print(f"model_config_id={mid}: FAIL - {e}")

    await channel.close()


asyncio.run(check())
