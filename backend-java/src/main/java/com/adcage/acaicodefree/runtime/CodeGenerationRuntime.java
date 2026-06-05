package com.adcage.acaicodefree.runtime;

import reactor.core.publisher.Flux;

public interface CodeGenerationRuntime {

    String getName();

    Flux<String> stream(CodeGenerationRequest request);
}
