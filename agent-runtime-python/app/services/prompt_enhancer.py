import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.exceptions import AgentRuntimeError
from app.services.chat_model_factory import ChatModelFactory

logger = logging.getLogger("app.services.prompt_enhancer")

ENHANCE_SYSTEM_PROMPT = """你是一个网页生成提示词增强助手。

任务：
1. 读取用户原始网站需求。
2. 如果有图片摘要信息，结合图片信息优化提示词；如果没有图片信息，仅基于用户需求进行增强。
3. 输出一个更具体、更容易用于网页生成的增强提示词。

要求：
1. 强调页面结构、视觉风格、重点模块和交互细节。
2. 不要照抄全部图片链接，只保留对页面生成有帮助的摘要。
3. 输出纯文本，不要使用 Markdown 标题。
4. 内容要紧凑，避免空话。
5. 如果用户需求较简短，请补充合理的页面结构、配色建议、布局细节等内容。"""


class PromptEnhancerService:
    def __init__(self, chat_model_factory: ChatModelFactory):
        self.chat_model_factory = chat_model_factory

    async def enhance(self, prompt: str, model_config: dict) -> str:
        if not prompt or not prompt.strip():
            raise AgentRuntimeError("提示词不能为空")

        chat_model: BaseChatModel = self.chat_model_factory.create(model_config)

        messages = [
            {"role": "system", "content": ENHANCE_SYSTEM_PROMPT},
            {"role": "user", "content": f"请优化以下网页生成提示词：\n\n{prompt}"},
        ]

        try:
            response = await chat_model.ainvoke(messages)
            content = response.content
            if not content or not content.strip():
                logger.warning("enhance prompt returned empty, returning original")
                return prompt
            return content.strip()
        except Exception as e:
            logger.error("enhance prompt failed: %s", e)
            raise AgentRuntimeError(f"提示词优化失败: {e}") from e
