package com.adcage.acaicodefree.workflow.ai;

import com.adcage.acaicodefree.workflow.model.ImageResource;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

import java.util.List;

public interface ImageCollectionService {

    @SystemMessage(fromResource = "prompt/image-collection-system-prompt.txt")
    List<ImageResource> collectImages(@UserMessage String userPrompt);
}
