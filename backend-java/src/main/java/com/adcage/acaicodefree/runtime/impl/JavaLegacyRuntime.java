package com.adcage.acaicodefree.runtime.impl;

import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class JavaLegacyRuntime implements CodeGenerationRuntime {

    private static final String NAME = "java-legacy";

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public Flux<String> stream(CodeGenerationRequest request) {
        return Flux.error(new UnsupportedOperationException("JavaLegacyRuntime.stream 尚未接入，请通过 AppServiceImpl 直接调用"));
    }
}
