package com.adcage.acaicodefree.config.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RoutingChatModelConfig {

    @Value("${app.ai.routing.base-url}")
    private String baseUrl;

    @Value("${app.ai.routing.api-key:}")
    private String apiKey;

    @Value("${app.ai.routing.model-name}")
    private String modelName;

    @Value("${app.ai.routing.max-tokens:100}")
    private Integer maxTokens;

    @Value("${app.ai.routing.temperature:0.0}")
    private Double temperature;

    @Value("${app.ai.routing.max-retries:3}")
    private Integer maxRetries;

    @Bean("routingChatModel")
    public ChatLanguageModel routingChatModel() {
        return OpenAiChatModel.builder()
                .baseUrl(baseUrl)
                .apiKey(apiKey)
                .modelName(modelName)
                .maxTokens(maxTokens)
                .temperature(temperature)
                .maxRetries(maxRetries)
                .logRequests(false)
                .logResponses(false)
                .build();
    }
}
