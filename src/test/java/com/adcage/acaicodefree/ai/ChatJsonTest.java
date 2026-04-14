package com.adcage.acaicodefree.ai;

import dev.langchain4j.model.chat.request.ChatRequest;
import dev.langchain4j.model.openai.OpenAiChatModel;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("local")
@Slf4j
public class ChatJsonTest {
    @Resource
    private AiCodeGeneratorService aiService;

    @Value("${langchain4j.open-ai.chat-model.base-url}")
    private String baseUrl;

    @Value("${langchain4j.open-ai.chat-model.api-key}")
    private String apiKey;

    @Value("${langchain4j.open-ai.chat-model.model-name}")
    private String modelName;

    @Value("${langchain4j.open-ai.chat-model.response-format:json}")
    private String responseFormat;


    @Test
    public void test() {
        Assumptions.assumeTrue(apiKey != null && !apiKey.isBlank() && !"<your-api-key>".equals(apiKey), "未配置可用 API Key，跳过测试");
        OpenAiChatModel openAiChatModel = OpenAiChatModel.builder()
                .baseUrl(baseUrl)
                .apiKey(apiKey)
                .modelName(modelName)
                .responseFormat(responseFormat)
                .logRequests(true)
                .build();
        String chat = openAiChatModel.chat("你好,响应数据格式为{" +
                "response:回答" +
                "}");
        Assertions.assertNotNull(chat);
        Assertions.assertFalse(chat.isBlank());
        System.out.println(chat);
    }

    @Test
    public void test2() {
        String chat = aiService.chat("你好");
        System.out.println(chat);
    }
}
