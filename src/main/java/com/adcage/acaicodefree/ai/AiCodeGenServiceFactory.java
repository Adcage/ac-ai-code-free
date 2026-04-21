package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.ai.tools.ToolManager;
import com.adcage.acaicodefree.core.memory.ChatMemoryLoader;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.chat.StreamingChatLanguageModel;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.concurrent.TimeUnit;

@Component
public class AiCodeGenServiceFactory {

    private static final Logger log = LoggerFactory.getLogger(AiCodeGenServiceFactory.class);

    @Resource
    private ChatLanguageModel chatModel;

    @Resource(name = "openAiStreamingChatModel")
    private StreamingChatLanguageModel legacyStreamingChatLanguageModel;

    @Resource(name = "reasoningStreamingChatModel")
    private StreamingChatLanguageModel reasoningStreamingChatModel;

    @Resource
    private ToolManager toolManager;

    @Resource
    private ObjectProvider<ChatMemoryLoader> chatMemoryLoaderProvider;

    @Value("${app.ai.vue-project.memory-window-size:20}")
    private int memoryWindowSize;

    private final Cache<String, AiCodeGeneratorService> serviceCache = Caffeine.newBuilder()
            .maximumSize(1000)
            .expireAfterWrite(30, TimeUnit.MINUTES)
            .expireAfterAccess(10, TimeUnit.MINUTES)
            .build();

    public AiCodeGeneratorService getService(Long appId, CodeGenTypeEnum codeGenType) {
        String cacheKey = buildCacheKey(appId, codeGenType);
        return serviceCache.get(cacheKey, ignored -> createService(appId, codeGenType));
    }

    String buildCacheKey(Long appId, CodeGenTypeEnum codeGenType) {
        return appId + ":" + codeGenType.getValue();
    }

    private AiCodeGeneratorService createService(Long appId, CodeGenTypeEnum codeGenType) {
        if (codeGenType == CodeGenTypeEnum.VUE_PROJECT) {
            return createVueProjectService(appId);
        }
        return createLegacyService();
    }

    protected AiCodeGeneratorService createLegacyService() {
        return AiServices.builder(AiCodeGeneratorService.class)
                .chatLanguageModel(chatModel)
                .streamingChatLanguageModel(legacyStreamingChatLanguageModel)
                .build();
    }

    protected AiCodeGeneratorService createVueProjectService(Long appId) {
        return AiServices.builder(AiCodeGeneratorService.class)
                .chatLanguageModel(chatModel)
                .streamingChatLanguageModel(reasoningStreamingChatModel)
                .tools(toolManager.getAllTools())
                .chatMemoryProvider(memoryId -> resolveChatMemory(memoryId, appId))
                .build();
    }

    ChatMemory resolveChatMemory(Object memoryId, Long appId) {
        Long currentAppId;
        if (memoryId instanceof Long longMemoryId) {
            currentAppId = longMemoryId;
        } else {
            currentAppId = appId;
        }

        ChatMemoryLoader chatMemoryLoader = chatMemoryLoaderProvider.getIfAvailable();
        if (chatMemoryLoader == null) {
            log.warn("ChatMemoryLoader bean unavailable during restart, fallback to in-memory chat window");
            return MessageWindowChatMemory.withMaxMessages(memoryWindowSize);
        }
        return chatMemoryLoader.load(currentAppId);
    }
}
