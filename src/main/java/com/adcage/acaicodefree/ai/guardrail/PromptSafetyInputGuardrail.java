package com.adcage.acaicodefree.ai.guardrail;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.regex.Pattern;

@Component
public class PromptSafetyInputGuardrail {

    private static final int MAX_LENGTH = 2000;

    private static final List<String> INJECTION_KEYWORDS = List.of(
            "忽略之前指令", "忽略以上指令", "ignore previous instructions", "ignore above",
            "bypass", "jailbreak", "DAN mode"
    );

    private static final List<Pattern> INJECTION_PATTERNS = List.of(
            Pattern.compile("you are (now|a) (system|admin|root)", Pattern.CASE_INSENSITIVE),
            Pattern.compile("(show|reveal|display|print).*(prompt|system message|instruction)", Pattern.CASE_INSENSITIVE),
            Pattern.compile("ignore (safety|security|filter|guardrail)", Pattern.CASE_INSENSITIVE)
    );

    public void validate(String userMessage) {
        if (StrUtil.isBlank(userMessage)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "请输入有效内容");
        }
        if (userMessage.length() > MAX_LENGTH) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "输入内容过长，请精简后重试");
        }
        String lowerText = userMessage.toLowerCase();
        for (String keyword : INJECTION_KEYWORDS) {
            if (lowerText.contains(keyword.toLowerCase())) {
                throw new BusinessException(ErrorCode.PARAMS_ERROR, "输入内容包含不安全指令，请修改后重试");
            }
        }
        for (Pattern pattern : INJECTION_PATTERNS) {
            if (pattern.matcher(userMessage).find()) {
                throw new BusinessException(ErrorCode.PARAMS_ERROR, "输入内容包含不安全指令，请修改后重试");
            }
        }
    }
}
