package com.adcage.acaicodefree.legacy.ai.guardrail;

import cn.hutool.core.util.StrUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
@Deprecated
public class RetryOutputGuardrail {

    private static final Logger log = LoggerFactory.getLogger(RetryOutputGuardrail.class);

    private static final int MIN_MEANINGFUL_LENGTH = 5;

    public OutputCheckResult validate(String output) {
        if (StrUtil.isBlank(output)) {
            log.warn("输出护栏: 模型返回为空");
            return OutputCheckResult.failure("模型返回为空，请重试");
        }
        if (output.trim().length() < MIN_MEANINGFUL_LENGTH
                && !output.matches(".*[a-zA-Z\\u4e00-\\u9fa5].*")) {
            log.warn("输出护栏: 模型返回内容过短且无意义, output={}", output);
            return OutputCheckResult.failure("模型返回内容过短，请重试");
        }
        return OutputCheckResult.success();
    }

    public static class OutputCheckResult {

        private final boolean valid;
        private final String errorMessage;

        private OutputCheckResult(boolean valid, String errorMessage) {
            this.valid = valid;
            this.errorMessage = errorMessage;
        }

        public static OutputCheckResult success() {
            return new OutputCheckResult(true, null);
        }

        public static OutputCheckResult failure(String errorMessage) {
            return new OutputCheckResult(false, errorMessage);
        }

        public boolean isValid() {
            return valid;
        }

        public String getErrorMessage() {
            return errorMessage;
        }
    }
}
