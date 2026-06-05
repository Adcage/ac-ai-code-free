from fastapi import APIRouter

from app.api.code_generation import router as code_generation_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(code_generation_router)
