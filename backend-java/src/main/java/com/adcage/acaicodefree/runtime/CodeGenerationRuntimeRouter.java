package com.adcage.acaicodefree.runtime;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class CodeGenerationRuntimeRouter {

    private final List<CodeGenerationRuntime> runtimes;

    @Value("${agent.runtime:java-legacy}")
    private String runtimeName;

    public CodeGenerationRuntimeRouter(List<CodeGenerationRuntime> runtimes) {
        this.runtimes = runtimes;
    }

    public CodeGenerationRuntime select() {
        return runtimes.stream()
                .filter(runtime -> runtime.getName().equalsIgnoreCase(runtimeName))
                .findFirst()
                .orElseThrow(() -> new BusinessException(ErrorCode.SYSTEM_ERROR, "未找到代码生成运行时：" + runtimeName));
    }
}
