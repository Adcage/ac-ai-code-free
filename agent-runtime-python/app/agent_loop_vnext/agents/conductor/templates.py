"""Conductor Agent 系统模板。

每个模板由系统硬编码，保证子 Agent 收到必要的上下文信息。
PM（Conductor）的补充说明通过模板中的 {pm_notes} 注入。
"""

# Planner 模板：技术规划，输出 .agent/spec.md（第一个被调用，前序摘要为空）
PLANNER_TASK_TEMPLATE = """## 用户需求
{user_prompt}

{previous_summary}## PM 补充说明
{pm_notes}

## 任务
请理解用户需求，进行技术规划，输出 .agent/spec.md。

## 输出标准
.agent/spec.md 必须包含：
1. 项目结构（目录树）
2. 页面/模块清单（每个页面的功能说明）
3. 技术选型确认
4. 路由方案
5. 状态管理方案

## 约束
- 如果需求信息不足以规划，请直接返回 needs_clarification
- 不要猜测用户未明确说明的需求
- 完成后返回一句话摘要（不超过 100 字）
"""

# Implementor 模板：代码实现
IMPLEMENTOR_TASK_TEMPLATE = """## 用户需求
{user_prompt}

{previous_summary}
## PM 补充说明
{pm_notes}

## 任务
请基于用户需求进行实现。如果需要了解项目结构或现有代码，自行使用 Glob/Grep/Read 查看。

## 输出标准
1. 完成后用 Build 命令验证（如 npm run build、npm run type-check）
2. 返回一句话摘要（不超过 100 字）
"""

# Validator 模板：校验 + 修复
VALIDATOR_TASK_TEMPLATE = """## 用户需求
{user_prompt}

{previous_summary}
## PM 补充说明
{pm_notes}

## 任务
请对照 .agent/spec.md（如果有）检查代码完整性，发现小问题用 Edit 修复。
修复后运行构建验证（如 npm run build）。

## 输出标准
- 检查通过：直接返回 "校验通过"
- 修复后通过：返回 "修复完成，构建通过"
- 修复失败：返回 "修复失败" + 具体原因

## 约束
- 只能修改已有文件，不要创建新文件
- 不要使用 Write 工具
"""

# 按 Agent 名称映射
TASK_TEMPLATES = {
    "planner": PLANNER_TASK_TEMPLATE,
    "implementor": IMPLEMENTOR_TASK_TEMPLATE,
    "validator": VALIDATOR_TASK_TEMPLATE,
}
