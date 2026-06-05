package com.adcage.acaicodefree.runtime.impl;

import com.adcage.acaicodefree.config.properties.WorkspaceProperties;
import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
public class PythonAgentRuntime implements CodeGenerationRuntime {

    private static final String NAME = "python-agent";

    @Value("${agent.python.base-url:http://localhost:9000}")
    private String pythonBaseUrl;

    @Resource
    private WorkspaceProperties workspaceProperties;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        WebClient webClient = WebClient.builder()
                .baseUrl(pythonBaseUrl)
                .build();

        Map<String, Object> body = new HashMap<>();
        body.put("agentRunId", String.valueOf(request.getAgentRunId()));
        body.put("appId", request.getAppId());
        body.put("sessionId", request.getSessionId());
        body.put("userId", request.getLoginUser().getId());
        body.put("prompt", request.getMessage());
        body.put("codeGenType", request.getApp().getCodeGenType());
        body.put("workspacePath", resolveWorkspacePath(request.getAgentRunId()));
        if (request.getApp() != null) {
            body.put("modelConfigId", null);
            body.put("configVersion", null);
        }

        return webClient.post()
                .uri("/agent/code-generation/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .bodyToFlux(String.class)
                .doOnError(e -> log.error("Python Agent Runtime 调用失败: {}", e.getMessage(), e));
    }

    private String resolveWorkspacePath(Long agentRunId) {
        if (agentRunId == null) {
            return workspaceProperties.getAgentWorkspaceDir() + "/unknown/source";
        }
        return workspaceProperties.getAgentWorkspaceDir() + "/" + agentRunId + "/source";
    }
}
