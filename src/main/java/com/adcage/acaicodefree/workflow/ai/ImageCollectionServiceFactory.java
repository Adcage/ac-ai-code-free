package com.adcage.acaicodefree.workflow.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import com.adcage.acaicodefree.workflow.tool.ImageSearchTool;
import com.adcage.acaicodefree.workflow.tool.LogoGeneratorTool;
import com.adcage.acaicodefree.workflow.tool.MermaidDiagramTool;
import com.adcage.acaicodefree.workflow.tool.UndrawIllustrationTool;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

@Component
public class ImageCollectionServiceFactory {

    @Resource
    private ChatLanguageModel chatLanguageModel;

    @Resource
    private ImageSearchTool imageSearchTool;

    @Resource
    private UndrawIllustrationTool undrawIllustrationTool;

    @Resource
    private MermaidDiagramTool mermaidDiagramTool;

    @Resource
    private LogoGeneratorTool logoGeneratorTool;

    public ImageCollectionService createService() {
        return AiServices.builder(ImageCollectionService.class)
                .chatLanguageModel(chatLanguageModel)
                .tools(imageSearchTool, undrawIllustrationTool, mermaidDiagramTool, logoGeneratorTool)
                .build();
    }
}
