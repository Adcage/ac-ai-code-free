package com.adcage.acaicodefree.legacy.workflow.ai;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

/**
 * @deprecated Java workflow prompt 增强已禁用，提示词增强必须通过 Python Agent Runtime。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
public interface PromptEnhancerService {

    @SystemMessage(fromResource = "prompt/workflow-prompt-enhancer-system-prompt.txt")
    String enhancePrompt(@UserMessage String originalPrompt, @UserMessage String imageSummary);
}
