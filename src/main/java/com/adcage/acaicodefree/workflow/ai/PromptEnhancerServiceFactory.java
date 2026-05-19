package com.adcage.acaicodefree.workflow.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

@Component
public class PromptEnhancerServiceFactory {

    @Resource
    private ChatLanguageModel chatLanguageModel;

    public PromptEnhancerService createService() {
        return AiServices.builder(PromptEnhancerService.class)
                .chatLanguageModel(chatLanguageModel)
                .build();
    }
}
