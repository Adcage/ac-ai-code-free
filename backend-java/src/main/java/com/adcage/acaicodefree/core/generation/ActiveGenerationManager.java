package com.adcage.acaicodefree.core.generation;

import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Component;

import java.util.concurrent.ConcurrentHashMap;

/**
 * 管理所有活跃的生成任务。
 * key = sessionId，value = ActiveGeneration。
 * 生成完成后由调用方 remove，PreDestroy 时自动清理所有残留。
 */
@Component
public class ActiveGenerationManager {

    private final ConcurrentHashMap<Long, ActiveGeneration> generations = new ConcurrentHashMap<>();

    public ActiveGeneration register(Long sessionId, Long agentRunId) {
        return generations.computeIfAbsent(sessionId, k -> new ActiveGeneration(k, agentRunId));
    }

    public ActiveGeneration get(Long sessionId) {
        return generations.get(sessionId);
    }

    public String getAccumulatedText(Long sessionId) {
        ActiveGeneration gen = generations.get(sessionId);
        return gen != null ? gen.getText() : null;
    }

    public void remove(Long sessionId) {
        generations.remove(sessionId);
    }

    @PreDestroy
    public void clear() {
        generations.clear();
    }
}
