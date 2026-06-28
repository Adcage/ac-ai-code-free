package com.adcage.acaicodefree.core.handler;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.ai.model.message.StreamMessageTypeEnum;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

/**
 * SSE 流处理器：将 JSON 消息流转换为可读文本。
 *
 * 职责：
 * - ai_response → 累积到 readableOutput（纯 AI 文本）
 * - tool_request / tool_executed / status → 静默通过（不污染 readableOutput）
 * - 工具调用已由 GrpcPythonAgentRuntime 采集后结构化入库（extra.toolCalls）
 */
@Component
public class JsonMessageStreamHandler {

    public Flux<String> handle(Flux<String> stream, StringBuilder readableOutput) {
        return stream.flatMap(chunk -> {
            if (StrUtil.isBlank(chunk)) {
                return Flux.empty();
            }
            JSONObject jsonObject;
            try {
                jsonObject = JSONUtil.parseObj(chunk);
            } catch (Exception e) {
                readableOutput.append(chunk);
                return Flux.just(chunk);
            }
            String type = jsonObject.getStr("type");
            if (StreamMessageTypeEnum.AI_RESPONSE.getValue().equals(type)) {
                String data = jsonObject.getStr("data", "");
                if ("waiting_for_user".equals(data) || data.startsWith("Agent loop completed:")) {
                    return Flux.just(chunk);
                }
                readableOutput.append(data);
                return Flux.just(chunk);
            }
            // tool_request / tool_executed / status / workflow_event
            // 不再写入 readableOutput，工具调用已由 GrpcPythonAgentRuntime 采集
            return Flux.just(chunk);
        });
    }
}
