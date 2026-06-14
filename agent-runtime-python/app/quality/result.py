from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    id: str
    status: str
    severity: str
    message: str
    file_path: str = ""
