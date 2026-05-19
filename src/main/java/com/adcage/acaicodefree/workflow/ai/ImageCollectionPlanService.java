package com.adcage.acaicodefree.workflow.ai;

import com.adcage.acaicodefree.workflow.model.ImageCollectionPlan;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

public interface ImageCollectionPlanService {

    @SystemMessage(fromResource = "prompt/image-collection-plan-system-prompt.txt")
    ImageCollectionPlan buildPlan(@UserMessage String userPrompt);
}
