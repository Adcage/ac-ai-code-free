package com.adcage.acaicodefree.ai;

import dev.langchain4j.model.chat.request.ChatRequest;
import dev.langchain4j.model.openai.OpenAiChatModel;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;

@Slf4j
public class ChatJsonTest {
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
}
