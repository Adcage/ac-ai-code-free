package com.adcage.acaicodefree.core.memory;

import com.adcage.acaicodefree.mapper.ChatHistoryMapper;
import com.adcage.acaicodefree.model.entity.ChatHistory;
import com.mybatisflex.core.query.QueryWrapper;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import jakarta.annotation.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * @deprecated Java LangChain4j chat memory 已随 Java AI 核心禁用，保留仅用于历史迁移参考。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
@Component
public class ChatMemoryLoader {

    @Resource
    private ChatHistoryMapper chatHistoryMapper;

    @Value("${app.ai.vue-project.memory-window-size:20}")
    private Integer memoryWindowSize;

    public ChatMemory load(Long appId) {
        MessageWindowChatMemory chatMemory = MessageWindowChatMemory.withMaxMessages(memoryWindowSize);
        if (appId == null || appId <= 0) {
            return chatMemory;
        }
        List<ChatHistory> historyList = chatHistoryMapper.selectListByQuery(QueryWrapper.create()
                .eq("appId", appId)
                .in("messageType", "user", "ai")
                .orderBy("createTime", false)
                .limit(memoryWindowSize));
        if (historyList == null || historyList.isEmpty()) {
            return chatMemory;
        }
        List<ChatHistory> orderedHistory = new ArrayList<>(historyList);
        Collections.reverse(orderedHistory);
        for (ChatHistory history : orderedHistory) {
            if ("user".equals(history.getMessageType())) {
                chatMemory.add(UserMessage.from(history.getMessage()));
            } else if ("ai".equals(history.getMessageType())) {
                chatMemory.add(AiMessage.from(history.getMessage()));
            }
        }
        return chatMemory;
    }
}
