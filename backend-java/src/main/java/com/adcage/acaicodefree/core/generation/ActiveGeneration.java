package com.adcage.acaicodefree.core.generation;

import reactor.core.publisher.Sinks;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/**
 * 内存中保存的活跃生成状态。
 * 每个 session 对应一个实例，生成完成后写 DB 并移除。
 */
public class ActiveGeneration {

    private final Long sessionId;
    private final Long agentRunId;
    private final StringBuilder accumulatedText = new StringBuilder();
    private final List<Map<String, Object>> toolCalls = new ArrayList<>();
    private final long startTime = System.currentTimeMillis();
    private volatile boolean completed = false;

    /** 当前生成的 Sink，供 SSE 重连时新订阅者续流 */
    private Sinks.Many<String> sink;

    /** gRPC 流完成时的回调，由 AppServiceImpl 注册，内部订阅者触发 */
    private Consumer<String> onGenerationCompleted;

    public ActiveGeneration(Long sessionId, Long agentRunId) {
        this.sessionId = sessionId;
        this.agentRunId = agentRunId;
    }

    public void appendText(String text) {
        accumulatedText.append(text);
    }

    public String getText() {
        return accumulatedText.toString();
    }

    public void addToolCall(Map<String, Object> toolCall) {
        toolCalls.add(toolCall);
    }

    public List<Map<String, Object>> getToolCalls() {
        return toolCalls;
    }

    public Long getSessionId() {
        return sessionId;
    }

    public Long getAgentRunId() {
        return agentRunId;
    }

    public boolean isCompleted() {
        return completed;
    }

    public void setCompleted(boolean completed) {
        this.completed = completed;
    }

    public long getStartTime() {
        return startTime;
    }

    // ---- sink (供重连用) ----

    public void setSink(Sinks.Many<String> sink) {
        this.sink = sink;
    }

    public Sinks.Many<String> getSink() {
        return sink;
    }

    // ---- 完成回调 ----

    public void setOnGenerationCompleted(Consumer<String> callback) {
        this.onGenerationCompleted = callback;
    }

    /** 调用完成回调。由 GrpcPythonAgentRuntime 的内部订阅者在 onComplete/onError 时触发。 */
    public void fireGenerationCompleted(String finalText) {
        if (onGenerationCompleted != null) {
            onGenerationCompleted.accept(finalText);
        }
    }
}
