package com.adcage.acaicodefree.workflow.ai;

import com.adcage.acaicodefree.workflow.model.ImageResource;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

import java.util.List;

/**
 * @deprecated Java workflow 图片采集 AI 服务已禁用，AI 规划能力必须迁移到 Python Agent Runtime。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
public interface ImageCollectionService {

    @SystemMessage(fromResource = "prompt/image-collection-system-prompt.txt")
    List<ImageResource> collectImages(@UserMessage String userPrompt);
}
