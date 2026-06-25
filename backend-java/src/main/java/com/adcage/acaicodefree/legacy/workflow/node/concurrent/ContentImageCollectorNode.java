package com.adcage.acaicodefree.legacy.workflow.node.concurrent;

import com.adcage.acaicodefree.legacy.workflow.model.ImageCollectionPlan;
import com.adcage.acaicodefree.legacy.workflow.model.ImageResource;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

@Deprecated
public class ContentImageCollectorNode {

    private final Function<String, List<ImageResource>> collector;

    public ContentImageCollectorNode(Function<String, List<ImageResource>> collector) {
        this.collector = collector;
    }

    public Map<String, Object> apply(AgentState state) {
        ImageCollectionPlan plan = WorkflowContext.fromState(state).getImageCollectionPlan();
        List<ImageResource> result = plan == null || plan.getContentQuery() == null ? Collections.emptyList() : collector.apply(plan.getContentQuery());
        return Map.of("contentImages", result);
    }
}
