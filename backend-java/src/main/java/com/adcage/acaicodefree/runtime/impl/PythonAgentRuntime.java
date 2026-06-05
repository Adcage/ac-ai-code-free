package com.adcage.acaicodefree.runtime.impl;

import com.adcage.acaicodefree.config.properties.WorkspaceProperties;
import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
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

    private final HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        return Flux.create(sink -> {
            try {
                Map<String, Object> body = new HashMap<>();
                body.put("agentRunId", String.valueOf(request.getAgentRunId()));
                body.put("appId", request.getAppId());
                body.put("sessionId", request.getSessionId());
                body.put("userId", request.getLoginUser().getId());
                body.put("prompt", request.getMessage());
                body.put("codeGenType", request.getApp().getCodeGenType());
                body.put("workspacePath", resolveWorkspacePath(request.getAgentRunId()));

                String jsonBody = objectMapper.writeValueAsString(body);

                HttpRequest httpRequest = HttpRequest.newBuilder()
                        .uri(URI.create(pythonBaseUrl + "/agent/code-generation/stream"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                        .build();

                HttpResponse<Void> response = httpClient.send(
                        httpRequest,
                        HttpResponse.BodyHandlers.discarding()
                );

                if (response.statusCode() != 200) {
                    sink.error(new RuntimeException("Python Agent Runtime 返回错误状态码: " + response.statusCode()));
                    return;
                }

                sink.complete();
            } catch (Exception e) {
                log.error("Python Agent Runtime 调用失败: {}", e.getMessage(), e);
                sink.error(e);
            }
        });
    }

    private String resolveWorkspacePath(Long agentRunId) {
        if (agentRunId == null) {
            return workspaceProperties.getAgentWorkspaceDir() + "/unknown/source";
        }
        return workspaceProperties.getAgentWorkspaceDir() + "/" + agentRunId + "/source";
    }
}
