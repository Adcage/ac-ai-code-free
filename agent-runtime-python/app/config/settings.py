from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    java_platform_base_url: str = "http://localhost:8700/api"
    agent_runtime_name: str = "python-langgraph"


settings = Settings()
