package com.adcage.acaicodefree.ai;

import dev.langchain4j.model.chat.request.ChatRequest;
import dev.langchain4j.model.openai.OpenAiChatModel;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("local")
@Slf4j
public class ChatJsonTest {
    @Resource
    private AiCodeGeneratorService aiService;


    @Test
    public void test() {
        OpenAiChatModel openAiChatModel = OpenAiChatModel.builder()
                .baseUrl("https://api.deepseek.com")
                .apiKey("###")
                .modelName("deepseek-chat")
                .responseFormat("json")
                .logRequests(true)
                .build();
        String chat = openAiChatModel.chat("你好,响应数据格式为{" +
                "response:回答" +
                "}");
        System.out.println(chat);
    }

    @Test
    public void test2() {
        String chat = aiService.chat("你好");
        System.out.println(chat);
    }
}
