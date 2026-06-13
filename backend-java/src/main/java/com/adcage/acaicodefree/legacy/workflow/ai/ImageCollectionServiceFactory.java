package com.adcage.acaicodefree.legacy.workflow.ai;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.service.AiServices;
import com.adcage.acaicodefree.legacy.workflow.tool.ImageSearchTool;
import com.adcage.acaicodefree.legacy.workflow.tool.LogoGeneratorTool;
import com.adcage.acaicodefree.legacy.workflow.tool.MermaidDiagramTool;
import com.adcage.acaicodefree.legacy.workflow.tool.UndrawIllustrationTool;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

/**
 * @deprecated Java workflow 图片采集 AI 工厂已禁用，保留仅用于历史迁移参考。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
@Component
public class ImageCollectionServiceFactory {

    @Resource(name = "routingChatModel")
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
