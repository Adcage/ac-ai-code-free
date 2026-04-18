package com.adcage.acaicodefree.config;

import dev.langchain4j.model.chat.StreamingChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiStreamingChatModel;
import jakarta.annotation.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.core.env.Profiles;

@Configuration
public class ReasoningStreamingChatModelConfig {

    @Value("${app.ai.vue-project.base-url}")
    private String baseUrl;

    @Value("${app.ai.vue-project.api-key:}")
    private String apiKey;

    @Value("${app.ai.vue-project.dev-model-name}")
    private String devModelName;

    @Value("${app.ai.vue-project.prod-model-name}")
    private String prodModelName;

    @Value("${app.ai.vue-project.dev-max-tokens}")
    private Integer devMaxTokens;

    @Value("${app.ai.vue-project.prod-max-tokens}")
    private Integer prodMaxTokens;

    @Resource
    private Environment environment;

    @Bean("reasoningStreamingChatModel")
    public StreamingChatLanguageModel reasoningStreamingChatModel() {
        boolean useDevModel = environment.acceptsProfiles(Profiles.of("local"));
        return OpenAiStreamingChatModel.builder()
                .baseUrl(baseUrl)
                .apiKey(apiKey)
                .modelName(useDevModel ? devModelName : prodModelName)
                .maxTokens(useDevModel ? devMaxTokens : prodMaxTokens)
                .logRequests(true)
                .logResponses(true)
                .build();
    }
}
