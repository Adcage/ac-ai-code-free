package com.adcage.acaicodefree.workflow.node.concurrent;

import com.adcage.acaicodefree.workflow.model.ImageCollectionPlan;
import com.adcage.acaicodefree.workflow.model.ImageResource;
import com.adcage.acaicodefree.workflow.state.WorkflowContext;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

public class IllustrationCollectorNode {

    private final Function<String, List<ImageResource>> collector;

    public IllustrationCollectorNode(Function<String, List<ImageResource>> collector) {
        this.collector = collector;
    }

    public Map<String, Object> apply(AgentState state) {
        ImageCollectionPlan plan = WorkflowContext.fromState(state).getImageCollectionPlan();
        List<ImageResource> result = plan == null || plan.getIllustrationQuery() == null ? Collections.emptyList() : collector.apply(plan.getIllustrationQuery());
        return Map.of("illustrations", result);
    }
}
