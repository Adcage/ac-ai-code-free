package com.adcage.acaicodefree.runtime.impl;

import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class PythonAgentRuntime implements CodeGenerationRuntime {

    private static final String NAME = "python-agent";

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        return Flux.error(new UnsupportedOperationException("PythonAgentRuntime 尚未实现，请先完成 Python Agent Runtime 集成"));
    }
}
