package com.adcage.acaicodefree.runtime;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import jakarta.annotation.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class CodeGenerationRuntimeRouter {

    private static final String DISABLED_JAVA_AGENT_RUNTIME = "java-agent";

    @Resource
    private List<CodeGenerationRuntime> runtimes;

    @Value("${agent.runtime:python-agent}")
    private String runtimeName;

    public CodeGenerationRuntime select() {
        if (DISABLED_JAVA_AGENT_RUNTIME.equalsIgnoreCase(runtimeName)) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "Java AI runtime 已禁用，请使用 python-agent");
        }
        return runtimes.stream()
                .filter(runtime -> runtime.getName().equalsIgnoreCase(runtimeName))
                .findFirst()
                .orElseThrow(() -> new BusinessException(ErrorCode.SYSTEM_ERROR, "未找到代码生成运行时：" + runtimeName));
    }
}
