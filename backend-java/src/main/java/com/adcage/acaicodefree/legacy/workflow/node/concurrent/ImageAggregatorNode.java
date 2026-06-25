package com.adcage.acaicodefree.legacy.workflow.node.concurrent;

import cn.hutool.core.collection.CollUtil;
import com.adcage.acaicodefree.legacy.workflow.model.ImageResource;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import org.bsc.langgraph4j.state.AgentState;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Deprecated
public class ImageAggregatorNode {

    @SuppressWarnings("unchecked")
    public Map<String, Object> apply(AgentState state) {
        WorkflowContext context = WorkflowContext.fromState(state);
        context.advanceStep("image_aggregator");
        List<ImageResource> contentImages = state.value("contentImages", List.of());
        List<ImageResource> illustrations = state.value("illustrations", List.of());
        List<ImageResource> diagrams = state.value("diagrams", List.of());
        List<ImageResource> logos = state.value("logos", List.of());
        context.setContentImages(new ArrayList<>(contentImages));
        context.setIllustrations(new ArrayList<>(illustrations));
        context.setDiagrams(new ArrayList<>(diagrams));
        context.setLogos(new ArrayList<>(logos));
        List<ImageResource> all = new ArrayList<>();
        if (CollUtil.isNotEmpty(contentImages)) all.addAll(contentImages);
        if (CollUtil.isNotEmpty(illustrations)) all.addAll(illustrations);
        if (CollUtil.isNotEmpty(diagrams)) all.addAll(diagrams);
        if (CollUtil.isNotEmpty(logos)) all.addAll(logos);
        context.setImageList(all);
        return context.toStateUpdate();
    }
}
