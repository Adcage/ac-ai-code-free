package com.adcage.acaicodefree.workflow.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

@Component
public class ImageCollectionPlanServiceFactory {

    @Resource(name = "routingChatModel")
    private ChatLanguageModel chatLanguageModel;

    public ImageCollectionPlanService createService() {
        return AiServices.builder(ImageCollectionPlanService.class)
                .chatLanguageModel(chatLanguageModel)
                .build();
    }
}
