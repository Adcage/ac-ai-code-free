import logging
from typing import Any

from app.prompts.modules import PromptModule

logger = logging.getLogger("app.prompts.asset_modules")


class ArtifactOutputContractModule(PromptModule):
    id = "artifact_output_contract"
    category = "strategic"

    def render(self, context: Any, state: Any) -> str:
        code_gen_type = getattr(context, "code_gen_type", None)
        # 优先使用 state 中推荐的应用类型
        recommended = getattr(state, "recommended_code_gen_type", None)
        type_value = recommended if recommended else (code_gen_type.value if code_gen_type else "unknown")

        base_rules = (
            "## Artifact Output Contract\n"
            "\n"
            "- 必须将真实项目文件写入工作区，不要在回复中输出代码内容或使用 artifact 标签。\n"
            "- 不要使用占位符内容如 'Metric A'、'Card 1'、'Lorem ipsum' 或 'Feature One'。\n"
            "- 运行时会在工具执行后收集产物清单。\n"
            "- 确保入口文件存在。\n"
        )

        type_specific = {
            "single_file": (
                "- Output mode: single HTML file.\n"
                "- Write one complete index.html with inline <style> and <script>.\n"
                "- All CSS must be in a single <style> block inside <head>.\n"
                "- All JS must be in a single <script> block before </body>.\n"
                "- No external CSS/JS files, no CDN links, no frameworks.\n"
                "- Use semantic HTML: <header>, <main>, <section>, <footer>.\n"
                "- Use CSS custom properties (variables) for repeated colors, spacing, and type scale.\n"
            ),
            "multi-file": (
                "- Output mode: multi-file HTML project.\n"
                "- Write exactly three files: index.html, style.css, script.js.\n"
                "- index.html references style.css via <link> and script.js via <script>.\n"
                "- No build tools, no package.json, no frameworks.\n"
                "- Use semantic HTML: <header>, <main>, <section>, <footer>.\n"
                "- Use CSS custom properties (variables) for repeated colors, spacing, and type scale.\n"
            ),
            "vue_project": (
                "- Output mode: Vue project.\n"
                "- Preserve the seed project structure unless the user explicitly asks to replace it.\n"
                "- Generate production-quality Vue 3 code with complete visible states.\n"
                "- Write real Vue SFC files (.vue) into the workspace.\n"
                "- Include loading, empty, error, and normal states for all data-dependent views.\n"
                "- Use CSS custom properties (variables) for repeated colors, spacing, and type scale.\n"
            ),
        }

        specific = type_specific.get(
            type_value,
            f"- Output mode: {type_value}. Follow the project rules above.\n",
        )
        return base_rules + specific
