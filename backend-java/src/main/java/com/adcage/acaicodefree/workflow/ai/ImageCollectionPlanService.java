package com.adcage.acaicodefree.workflow.ai;

import com.adcage.acaicodefree.workflow.model.ImageCollectionPlan;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

/**
 * @deprecated Java workflow 图片采集规划已禁用，AI 规划能力必须迁移到 Python Agent Runtime。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
public interface ImageCollectionPlanService {

    @SystemMessage(fromResource = "prompt/image-collection-plan-system-prompt.txt")
    ImageCollectionPlan buildPlan(@UserMessage String userPrompt);
}
