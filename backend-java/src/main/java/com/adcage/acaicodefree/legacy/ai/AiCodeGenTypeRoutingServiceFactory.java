package com.adcage.acaicodefree.legacy.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

/**
 * @deprecated Java LangChain4j 路由服务已禁用，保留仅用于历史代码参考。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
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
