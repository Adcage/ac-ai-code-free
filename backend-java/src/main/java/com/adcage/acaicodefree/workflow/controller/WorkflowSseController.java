package com.adcage.acaicodefree.workflow.controller;

import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

/**
 * @deprecated Java workflow AI 入口已禁用，AI 核心执行必须通过 Python Agent Runtime。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
@RestController
@RequestMapping("/workflow/sse")
public class WorkflowSseController {

    @GetMapping(value = "/execute", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> execute(@RequestParam Long appId, @RequestParam String message) {
        String data = JSONUtil.toJsonStr(java.util.Map.of(
                "code", ErrorCode.OPERATION_ERROR.getCode(),
                "message", "Java workflow AI 入口已禁用，请使用 Python Agent Runtime"
        ));
        return Flux.just(ServerSentEvent.<String>builder()
                .event("business-error")
                .data(data)
                .build());
    }
}
