class AgentRuntimeError(Exception):
    def __init__(self, message: str, code: int = 4001, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
