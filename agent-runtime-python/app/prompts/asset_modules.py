import logging
from typing import Any

from app.prompts.modules import PromptModule

logger = logging.getLogger("app.prompts.asset_modules")


class ArtifactOutputContractModule(PromptModule):
    id = "artifact_output_contract"

    def render(self, context: Any, state: Any) -> str:
        return (
            "## Artifact Contract\n"
            "\n"
            "Write real project files with tools. Do not only describe the result.\n"
            "\n"
            "The runtime will collect an artifact manifest after tool execution. To support this:\n"
            "- Ensure the entry file exists.\n"
            "- Keep generated source files under the workspace root.\n"
            "- Do not reference remote placeholder assets.\n"
            "- Do not leave empty sections, placeholder cards, or \"Metric A\" labels."
        )
