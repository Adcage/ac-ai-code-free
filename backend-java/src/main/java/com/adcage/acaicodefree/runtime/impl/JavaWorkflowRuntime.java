package com.adcage.acaicodefree.runtime.impl;

import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class JavaWorkflowRuntime implements CodeGenerationRuntime {

    private static final String NAME = "java-workflow";

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        return Flux.error(new UnsupportedOperationException("JavaWorkflowRuntime 尚未实现"));
    }
}
