package com.adcage.acaicodefree.workflow.node.concurrent;

import com.adcage.acaicodefree.workflow.ai.ImageCollectionPlanService;
import com.adcage.acaicodefree.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Map;

@Slf4j
public class ImagePlanNode {

    private final ImageCollectionPlanService imageCollectionPlanService;

    public ImagePlanNode(ImageCollectionPlanService imageCollectionPlanService) {
        this.imageCollectionPlanService = imageCollectionPlanService;
    }

    public Map<String, Object> apply(AgentState state) {
        WorkflowContext context = WorkflowContext.fromState(state);
        context.advanceStep("image_plan");
        context.setImageCollectionPlan(imageCollectionPlanService.buildPlan(context.getOriginalPrompt()));
        return context.toStateUpdate();
    }
}
