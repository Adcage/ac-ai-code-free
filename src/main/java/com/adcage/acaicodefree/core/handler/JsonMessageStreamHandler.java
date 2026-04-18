package com.adcage.acaicodefree.core.handler;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.ai.model.message.StreamMessageTypeEnum;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

import java.util.HashSet;
import java.util.Set;

@Component
public class JsonMessageStreamHandler {

    public Flux<String> handle(Flux<String> stream, StringBuilder readableOutput) {
        Set<String> printedToolRequestIds = new HashSet<>();
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
                readableOutput.append(data);
                return Flux.just(chunk);
            }
            if (StreamMessageTypeEnum.TOOL_REQUEST.getValue().equals(type)) {
                String id = jsonObject.getStr("id", "");
                if (!printedToolRequestIds.add(id)) {
                    return Flux.empty();
                }
                String path = extractPath(jsonObject.getStr("arguments", ""));
                if (StrUtil.isNotBlank(path)) {
                    readableOutput.append("\n准备写入文件 ").append(path);
                }
                return Flux.just(chunk);
            }
            if (StreamMessageTypeEnum.TOOL_EXECUTED.getValue().equals(type)) {
                String result = jsonObject.getStr("result", "");
                String path = extractPath(jsonObject.getStr("arguments", ""));
                if (StrUtil.isBlank(path)) {
                    path = extractPath(result);
                }
                if (StrUtil.isNotBlank(path)) {
                    readableOutput.append("\n已写入文件 ").append(path);
                } else if (StrUtil.isNotBlank(result)) {
                    readableOutput.append("\n").append(result);
                }
                return Flux.just(chunk);
            }
            readableOutput.append(chunk);
            return Flux.just(chunk);
        });
    }

    private String extractPath(String text) {
        if (StrUtil.isBlank(text)) {
            return "";
        }
        try {
            JSONObject arguments = JSONUtil.parseObj(text);
            String relativeFilePath = arguments.getStr("relativeFilePath");
            return StrUtil.blankToDefault(relativeFilePath, "");
        } catch (Exception ignored) {
        }
        String marker = "文件写入成功：";
        if (text.contains(marker)) {
            return text.substring(text.indexOf(marker) + marker.length()).trim();
        }
        return "";
    }
}
