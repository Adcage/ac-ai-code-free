class PromptBuilder:
    def build_vue_app_prompt(self, user_prompt: str) -> str:
        if not user_prompt:
            raise ValueError("用户需求不能为空")

        return (
            "你是一个专业的前端开发工程师。请根据以下用户需求，生成一个完整的 Vue 3 单文件组件（.vue 文件）。\n"
            "\n"
            "要求：\n"
            "1. 输出必须是合法的 Vue 3 单文件组件内容，包含 <template>、<script setup> 和 <style scoped> 三个部分。\n"
            "2. 输出内容将直接写入 src/App.vue 文件，因此请不要在输出中使用 markdown 代码围栏（```vue ... ```）包裹，只输出原始 .vue 文件内容。\n"
            "3. 组件应当功能完整、样式美观、代码规范。\n"
            "\n"
            f"用户需求：{user_prompt}"
        )
