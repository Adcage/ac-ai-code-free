import logging

from app.capabilities.templates.registry import TemplateRegistry
from app.capabilities.templates.types import TemplateDefinition

logger = logging.getLogger("app.capabilities.templates.selector")


class TemplateSelector:
    def select(
        self,
        code_gen_type: str,
        registry: TemplateRegistry | None = None,
        default_template_id: str = "",
    ) -> TemplateDefinition | None:
        if registry is None:
            return None

        if default_template_id:
            try:
                template = registry.get(default_template_id)
                if not template.code_gen_type or template.code_gen_type == code_gen_type:
                    return template
            except KeyError:
                pass

        for template in registry.all():
            if not template.code_gen_type or template.code_gen_type == code_gen_type:
                return template

        return None
