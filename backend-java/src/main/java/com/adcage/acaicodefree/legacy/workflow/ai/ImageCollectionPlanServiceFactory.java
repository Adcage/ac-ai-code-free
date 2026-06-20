package com.adcage.acaicodefree.legacy.workflow.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

/**
 * @deprecated Java workflow 图片采集规划工厂已禁用，保留仅用于历史迁移参考。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
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
