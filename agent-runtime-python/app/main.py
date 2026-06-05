from fastapi import FastAPI

from app.api.code_generation import router as code_generation_router
from app.config.settings import settings

app = FastAPI(title="AC AI Code Free Agent Runtime")
app.include_router(code_generation_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "runtime": settings.agent_runtime_name}


@app.get("/health/warmup")
async def warmup() -> dict[str, str]:
    return {"status": "warmed"}
