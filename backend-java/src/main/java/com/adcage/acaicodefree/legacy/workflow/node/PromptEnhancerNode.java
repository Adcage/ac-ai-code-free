package com.adcage.acaicodefree.legacy.workflow.node;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.legacy.workflow.ai.PromptEnhancerService;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Map;

@Slf4j
@Deprecated
public class PromptEnhancerNode {

    private final PromptEnhancerService promptEnhancerService;

    public PromptEnhancerNode() {
        this((originalPrompt, imageSummary) -> "");
    }

    public PromptEnhancerNode(PromptEnhancerService promptEnhancerService) {
        this.promptEnhancerService = promptEnhancerService;
    }

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        String imageSummary = StrUtil.blankToDefault(ctx.getImageListStr(), "");
        log.info("[PromptEnhancerNode] starting, originalPrompt={}", ctx.getOriginalPrompt());
        ctx.advanceStep("prompt_enhancer");
        try {
            String enhancedPrompt = promptEnhancerService.enhancePrompt(ctx.getOriginalPrompt(), imageSummary);
            ctx.setEnhancedPrompt(StrUtil.isNotBlank(enhancedPrompt)
                    ? enhancedPrompt
                    : buildFallbackPrompt(ctx.getOriginalPrompt(), imageSummary));
        } catch (Exception e) {
            log.warn("[PromptEnhancerNode] prompt enhancement failed", e);
            ctx.setEnhancedPrompt(buildFallbackPrompt(ctx.getOriginalPrompt(), imageSummary));
        }
        log.info("[PromptEnhancerNode] completed, enhancedPrompt length={}", ctx.getEnhancedPrompt().length());
        return ctx.toStateUpdate();
    }

    private String buildFallbackPrompt(String originalPrompt, String imageSummary) {
        if (StrUtil.isBlank(imageSummary)) {
            return StrUtil.blankToDefault(originalPrompt, "请生成一个结构清晰、视觉专业的网页");
        }
        return StrUtil.format("需求：{}。可参考的视觉素材：{}。请生成一个结构清晰、视觉专业的网页。",
                StrUtil.blankToDefault(originalPrompt, "请生成一个网页"), imageSummary);
    }
}
