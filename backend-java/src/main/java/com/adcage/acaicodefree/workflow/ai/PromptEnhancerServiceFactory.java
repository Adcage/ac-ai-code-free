package com.adcage.acaicodefree.workflow.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

/**
 * @deprecated Java workflow prompt 增强工厂已禁用，保留仅用于历史迁移参考。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
@Component
public class PromptEnhancerServiceFactory {

    @Resource(name = "routingChatModel")
    private ChatLanguageModel chatLanguageModel;

    public PromptEnhancerService createService() {
        return AiServices.builder(PromptEnhancerService.class)
                .chatLanguageModel(chatLanguageModel)
                .build();
    }
}
