package com.adcage.acaicodefree.runtime.impl;

import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import com.adcage.acaicodefree.workflow.service.WorkflowCodeGeneratorService;
import jakarta.annotation.Resource;
import reactor.core.publisher.Flux;

/**
 * @deprecated Java AI runtime 已禁用，AI 核心执行必须通过 Python Agent Runtime。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
public class JavaAgentRuntime implements CodeGenerationRuntime {

    private static final String NAME = "java-agent";

    @Resource
    private WorkflowCodeGeneratorService workflowCodeGeneratorService;

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        return workflowCodeGeneratorService.executeWorkflowWithFlux(request.getAppId(), request.getMessage());
    }
}
