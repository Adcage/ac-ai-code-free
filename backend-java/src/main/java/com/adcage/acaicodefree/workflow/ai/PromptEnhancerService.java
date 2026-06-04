package com.adcage.acaicodefree.workflow.ai;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

public interface PromptEnhancerService {

    @SystemMessage(fromResource = "prompt/workflow-prompt-enhancer-system-prompt.txt")
    String enhancePrompt(@UserMessage String originalPrompt, @UserMessage String imageSummary);
}
