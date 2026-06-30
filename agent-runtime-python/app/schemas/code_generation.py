from pydantic import BaseModel


class CodeGenerationRequest(BaseModel):
    agentRunId: str
    appId: int
    sessionId: int
    userId: int
    prompt: str
    codeGenType: str
    workspacePath: str | None = None
