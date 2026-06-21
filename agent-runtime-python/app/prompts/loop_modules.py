"""Agent Loop 大循环提示词模块：plan/implement/validate 工作流、校验反馈、工具列表、计划规范、用户需求、Skill 上下文。"""

from typing import Any

from app.prompts.modules import PromptModule


class PlanWorkflowModule(PromptModule):
    """plan 模式工作流指令，从 PLAN_MODE_SYSTEM_PROMPT 拆解。"""

    id = "plan_workflow"
    category = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        return getattr(state, "mode", "") == "plan"

    def render(self, context: Any, state: Any) -> str:
        return (
            "你处于规划模式（Plan Mode）。你的职责是充分理解用户需求，制定完整的实现计划，然后提交规划结果。\n"
            "\n"
            "**核心原则：plan 模式的价值在于搞清楚用户要什么。需求不明确时，必须先问清楚再做计划。**\n"
            "\n"
            "## 工作流\n"
            "\n"
            "**步骤 0：澄清需求（必须先判断）**\n"
            "\n"
            "如果用户需求不够清晰——只说了一句话、没有说明功能、没有描述页面内容——你必须发起选择式提问。\n"
            "\n"
            "**提问规则（必须严格遵守）：**\n"
            "- 使用单选模式\n"
            "- 提供至少 3 个、最多 5 个具体选项\n"
            "- 每个选项用简短的短语描述一种可能（如'登录注册页面'、'数据展示仪表盘'、'待办事项列表'）\n"
            "- 根据用户原始需求推断可能的意图来设计选项，不要把问题丢回给用户\n"
            "用户回答后，根据回答继续下面的步骤。\n"
            "如果用户需求已经非常明确（如详细描述了功能和布局），可以跳过此步骤直接进入步骤 1。\n"
            "\n"
            "**步骤 1：判断是否有 Skill（1 步）**\n"
            "\n"
            "- 如果有选中的 Skill：Skill 正文已在上方「已选择的 Skill」段落中加载，直接阅读即可，**不要再读取 SKILL.md**。如需参考布局/清单，按需读取参考文件。然后进入步骤 2。\n"
            "- 如果没有选中的 Skill：**直接进入步骤 2**，不要反复查看空工作区。\n"
            "\n"
            "**步骤 2：编写实现计划（1 步）**\n"
            "\n"
            "按照计划编写规范，写入实现计划。计划必须包含文件清单、生成顺序、技术选型和关键逻辑。\n"
            "\n"
            "**步骤 3：提交规划结果**\n"
            "\n"
            "计划写入后，提交当前阶段结果并停止，由编排层决定下一阶段。\n"
            "\n"
            "## 注意事项\n"
            "\n"
            "- 你只能使用规划类工具（读取文件、询问用户、选择 Skill、编写计划）\n"
            "- 工作区为空时不要反复查看目录，直接开始规划\n"
            "- 如果连续 3 步没有进展，立即写入当前理解并提交规划结果\n"
            "- 不要在 plan 模式反复徘徊，目标是最多 3-4 步内提交结果\n"
            "- 对于配色、字体间距等不影响功能结构的纯视觉细节，可以在已确认需求、项目规则限定的范围内选择具体值\n"
            "- **不要在回复中复述 Skill 原文内容**，只提取关键规则和约束用于指导实现，对用户可见的回复必须是简洁的中文摘要"
        )


class ImplementWorkflowModule(PromptModule):
    """implement 模式工作流指令。"""

    id = "implement_workflow"
    category = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        return getattr(state, "mode", "") == "implement"

    def render(self, context: Any, state: Any) -> str:
        outline_text = "暂无实现规划"
        outline = getattr(state, "implementation_outline", None)
        if outline:
            if isinstance(outline, dict):
                outline_text = outline.get("text", str(outline))
            else:
                outline_text = str(outline)

        code_gen_type = "unknown"
        recommended = getattr(state, "recommended_code_gen_type", None)
        if recommended:
            code_gen_type = recommended
        elif context and hasattr(context, "code_gen_type"):
            ct = getattr(context, "code_gen_type", None)
            if ct:
                code_gen_type = ct.value if hasattr(ct, "value") else str(ct)

        is_vue = code_gen_type == "vue_project"
        dependency_step = ""
        if is_vue:
            dependency_step = (
                "\n- 项目类型为 Vue 工程：所有文件写入后，如果终端工具可用，应安装依赖包；如果终端工具不可用，跳过此步。\n"
            )

        parts = [
            "你处于实现模式（Implement Mode）。你的职责是按照实施计划将项目代码写入工作区。\n",
            "\n**重要：进入 implement 模式后，专注于代码生成，不要再反复分析或重复读取已有文件。**\n",
            f"\n## 实施计划\n\n{outline_text}\n",
            "\n## 工作流 —— 新建\n",
            "\n- 按实施计划中列出的文件顺序逐一创建文件。\n",
            "- 每个文件一次性写入完整内容，不省略、不使用占位符。\n",
            "- 文件路径使用正斜杠 /。\n",
            "- 不需要为了确认空工作区而反复读取目录。\n",
            dependency_step,
            "- 所有计划文件创建完成后，提交完成结果并说明完成了什么。\n",
            "\n## 工作流 —— 修改\n",
            "\n- 先了解当前工作区的目录结构和已有文件。\n",
            "- 再读取需要修改的文件当前内容。\n",
            "- 只修改与当前需求直接相关的内容，保持未授权文件和既有行为不变。\n",
            "- 每次修改都写入完整的文件内容。\n",
            "- 修改完成后，提交完成结果并说明修改了什么。\n",
            "\n## 计划不完整时的处理\n",
            "\n如果实施计划缺少以下关键信息，不能继续实现：\n",
            "- 缺少架构决策（框架选择、路由方案、状态管理模式等）；\n",
            "- 缺少交互定义（页面跳转关系、表单行为、数据流向等）；\n",
            "- 缺少文件范围（需要哪些文件、每个文件的职责）；\n",
            "- 其他可能影响产品行为、结构或交互的未明确内容。\n",
            "\n遇到上述情况时，不得自行补全后继续实现，也不得提交完成结果。应提交重新规划请求并说明具体缺失内容，由编排层决定下一阶段。\n",
            "\n## 实现细节补全的边界\n",
            "\n- 只能在用户已确认的需求、项目规则和已批准的实施计划范围内补充实现细节。\n",
            "- 允许补全的非关键细节：配色微调、间距数值、字重选择等不影响功能和结构的视觉细节。\n",
            "- 任何可能影响产品行为、架构、交互、权限、文件范围或视觉方向的内容都必须先确认，不得自行决定。\n",
            "\n## 注意事项\n",
            "\n- 当前模式的可用能力见上方工具列表，具体工具名称和参数由系统动态提供。\n",
            "- 每个文件写入完整可运行的代码，不要在文件之间拆分不完整的片段。\n",
            "- 不要伪造工具执行结果。\n",
            "- 生成过程直奔主题，3-5 个文件内完成。\n",
            "- **不要在回复中复述 Skill 原文内容**，只引用关键规则和约束，对用户可见的回复必须是简洁的中文摘要。\n",
        ]

        return "".join(parts)


class ValidateWorkflowModule(PromptModule):
    """validate 模式工作流指令。"""

    id = "validate_workflow"
    category = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        return getattr(state, "mode", "") == "validate"

    def render(self, context: Any, state: Any) -> str:
        check_results_text = ""
        check_results = getattr(state, "validation_check_results", None)
        if check_results:
            lines = []
            for r in check_results:
                status = r.get("status", "?")
                icon = "✓" if status == "pass" else ("✗" if status == "fail" else "⚠")
                severity = r.get('severity', '')
                if status == "pass":
                    lines.append(f"{icon} {r.get('id', '?')}: {r.get('message', '')}")
                else:
                    lines.append(f"{icon} [{severity}] {r.get('id', '?')}: {r.get('message', '')}")
            check_results_text = "\n".join(lines)

        parts = [
            "你处于校验模式（Validate Mode）。你的职责是检查已生成的代码是否符合项目结构要求。\n",
            "\n",
            "## 工作流\n",
            "\n",
            "1. 首先执行项目结构校验，获取检查结果。\n",
            "2. 根据检查结果，如有必要可查看文件内容进一步了解详情。\n",
            "3. 综合判断后输出校验结论。\n",
            "\n",
            "## 校验判断规则\n",
            "\n",
            "- 如果存在 error 级别的失败（如入口文件缺失）：输出失败结论，列出问题和修复建议\n",
            "- 如果仅有 warning 级别的提醒（如占位符文本）：可接受，输出通过结论\n",
            "- 如果全部通过：输出通过结论\n",
            "\n",
            "**注意：3 步内必须输出校验结论。**",
        ]

        if check_results_text:
            parts.append(f"\n\n## 已缓存的检查结果\n\n{check_results_text}\n\n（已执行过结构校验，无需重复执行）")

        return "".join(parts)


class ValidateFeedbackModule(PromptModule):
    """校验失败反馈模块，在 implement 模式下展示校验问题。"""

    id = "validate_feedback"
    category = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        return (
            getattr(state, "mode", "") == "implement"
            and bool(getattr(state, "validation_failures", None))
        )

    def render(self, context: Any, state: Any) -> str:
        failures = getattr(state, "validation_failures", [])
        if not failures:
            return ""

        lines = ["## 校验反馈\n", "\n上次生成的代码存在以下问题，请修复后重新生成：\n"]
        for i, f in enumerate(failures, 1):
            lines.append(f"{i}. {f.get('issue', str(f))}")
            suggestion = f.get("suggestion", "")
            if suggestion:
                lines.append(f"   修复建议：{suggestion}")
        return "\n".join(lines)


class ToolListModule(PromptModule):
    """动态工具列表模块，在节点执行前注入工具列表。"""

    id = "tool_list"
    category = "strategic"

    def __init__(self, tools: list | tuple | None = None) -> None:
        super().__init__()
        self._tools: tuple = tuple(tools) if tools else ()

    def enabled(self, context: Any, state: Any) -> bool:
        return len(self._tools) > 0

    def render(self, context: Any, state: Any) -> str:
        from app.prompts.tool_summary import format_tool_summary

        return format_tool_summary(self._tools)


class PlanSpecModule(PromptModule):
    """计划编写规范模块。"""

    id = "plan_spec"
    category = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        return getattr(state, "mode", "") == "plan"

    def render(self, context: Any, state: Any) -> str:
        return (
            "## 计划编写规范\n"
            "\n"
            "请严格按照以下规范编写实现计划并写入状态。\n"
            "\n"
            "### 1. 文件清单\n"
            "\n"
            "列出所有需要创建的文件，每个文件包含：\n"
            "- **文件路径**（如 `src/App.vue`、`index.html`）\n"
            "- **文件职责**（一句话说明这个文件做什么）\n"
            "- **关键依赖**（依赖哪些其他文件或第三方库）\n"
            "\n"
            "### 2. 生成顺序\n"
            "\n"
            "按依赖关系排列文件生成顺序，被依赖的文件先创建。\n"
            "\n"
            "### 3. 技术选型\n"
            "\n"
            "- 框架选择（如 Vue / React / 纯 HTML）\n"
            "- 样式方案（如 Tailwind / CSS Modules / 内联样式）\n"
            "- 关键第三方库\n"
            "\n"
            "### 4. 关键逻辑\n"
            "\n"
            "- 核心交互逻辑\n"
            "- 数据流向\n"
            "- 特殊处理（如响应式适配、动画等）"
        )


class UserPromptModule(PromptModule):
    """用户需求段落模块。"""

    id = "user_prompt"
    category = "mandatory"

    def render(self, context: Any, state: Any) -> str:
        prompt = getattr(context, "prompt", "")
        return f"## 用户需求\n\n{prompt}"


class SkillContextModule(PromptModule):
    """Skill 上下文模块，替换 PlanStepNode/ImplementStepNode 中的内联 Skill 信息构建。"""

    id = "skill_context"
    category = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        caps = getattr(state, "selected_capabilities", None)
        if caps is not None and getattr(caps, "skill", None) is not None:
            return True
        index = getattr(state, "_asset_index", None)
        if index is None:
            return False
        skills = index.skill_registry.all()
        return bool(skills)

    def render(self, context: Any, state: Any) -> str:
        caps = getattr(state, "selected_capabilities", None)
        skill = getattr(caps, "skill", None) if caps is not None else None
        if skill is None:
            index = getattr(state, "_asset_index", None)
            if index is not None:
                skills = index.skill_registry.all()
                if skills:
                    lines = ["## 可用 Skill 列表\n", "\n你可以选择一个适合当前任务的 Skill。\n"]
                    for s in skills:
                        lines.append(f"- **{s.id}**: {s.description}")
                    return "\n".join(lines)
            return ""

        skill_dir = str(skill.source_path.parent)
        parts = [
            "## 已选择的 Skill\n",
            f"\n**{skill.name}** (ID: {skill.id}): {skill.description}\n",
            f"\nSkill 目录：`{skill_dir}`\n",
        ]

        if skill.body:
            parts.append(f"\n### Skill 规则（已加载，无需再读取 SKILL.md）\n\n{skill.body.strip()}\n")

        if skill.references:
            parts.append("\n### Skill 可用参考资源\n")
            parts.append("\n如需参考布局/清单，按需读取以下文件：")
            for ref in skill.references:
                parts.append(f"\n  - {ref}")
            parts.append("\n\n**注意：不要逐个读取所有参考文件，只按需读取最相关的。**")

        return "".join(parts)
