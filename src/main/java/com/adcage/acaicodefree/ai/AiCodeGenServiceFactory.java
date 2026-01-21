package com.adcage.acaicodefree.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.chat.StreamingChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

/**
 * AI服务创建工厂
 *
 * @author adcage
 * @description AiCodeGenServiceFactory
 */
@Component
@Slf4j
public class AiCodeGenServiceFactory {

    @Resource
    private ChatLanguageModel chatModel;

    @Resource
    private StreamingChatLanguageModel streamingChatLanguageModel;

    /**
     * 创建AI代码生成服务
     * @return AiCodeGeneratorService
     */
    @Bean
    public AiCodeGeneratorService createAiCodeGeneratorService() {
        return AiServices.builder(AiCodeGeneratorService.class)
                .chatLanguageModel(chatModel)
                .streamingChatLanguageModel(streamingChatLanguageModel)
                .build();
    }
}