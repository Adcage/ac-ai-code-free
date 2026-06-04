package com.adcage.acaicodefree.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

@Component
public class AiCodeGenTypeRoutingServiceFactory {

    @Resource(name = "routingChatModel")
    private ChatLanguageModel chatModel;

    public AiCodeGenTypeRoutingService createService() {
        return AiServices.builder(AiCodeGenTypeRoutingService.class)
                .chatLanguageModel(chatModel)
                .build();
    }
}
