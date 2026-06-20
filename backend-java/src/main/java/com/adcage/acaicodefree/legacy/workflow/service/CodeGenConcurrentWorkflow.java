package com.adcage.acaicodefree.legacy.workflow.service;

import com.adcage.acaicodefree.legacy.workflow.node.concurrent.*;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import org.bsc.langgraph4j.CompiledGraph;
import org.bsc.langgraph4j.StateGraph;
import org.bsc.langgraph4j.state.AgentState;
import org.bsc.langgraph4j.state.Channel;
import org.bsc.langgraph4j.state.Channels;

import java.util.ArrayList;
import java.util.Map;

import static org.bsc.langgraph4j.StateGraph.END;
import static org.bsc.langgraph4j.StateGraph.START;
import static org.bsc.langgraph4j.action.AsyncNodeAction.node_async;

public class CodeGenConcurrentWorkflow {

    private final ImagePlanNode imagePlanNode;
    private final ContentImageCollectorNode contentImageCollectorNode;
    private final IllustrationCollectorNode illustrationCollectorNode;
    private final DiagramCollectorNode diagramCollectorNode;
    private final LogoCollectorNode logoCollectorNode;
    private final ImageAggregatorNode imageAggregatorNode;

    public CodeGenConcurrentWorkflow(ImagePlanNode imagePlanNode,
                                     ContentImageCollectorNode contentImageCollectorNode,
                                     IllustrationCollectorNode illustrationCollectorNode,
                                     DiagramCollectorNode diagramCollectorNode,
                                     LogoCollectorNode logoCollectorNode,
                                     ImageAggregatorNode imageAggregatorNode) {
        this.imagePlanNode = imagePlanNode;
        this.contentImageCollectorNode = contentImageCollectorNode;
        this.illustrationCollectorNode = illustrationCollectorNode;
        this.diagramCollectorNode = diagramCollectorNode;
        this.logoCollectorNode = logoCollectorNode;
        this.imageAggregatorNode = imageAggregatorNode;
    }

    public CompiledGraph<AgentState> createWorkflow() throws Exception {
        Map<String, Channel<?>> schema = Map.of(
                WorkflowContext.STATE_KEY, Channels.base(WorkflowContext::new),
                "contentImages", Channels.base(ArrayList::new),
                "illustrations", Channels.base(ArrayList::new),
                "diagrams", Channels.base(ArrayList::new),
                "logos", Channels.base(ArrayList::new)
        );
        StateGraph<AgentState> graph = new StateGraph<>(schema, AgentState::new)
                .addNode("image_plan", node_async(imagePlanNode::apply))
                .addNode("content_image_collector", node_async(contentImageCollectorNode::apply))
                .addNode("illustration_collector", node_async(illustrationCollectorNode::apply))
                .addNode("diagram_collector", node_async(diagramCollectorNode::apply))
                .addNode("logo_collector", node_async(logoCollectorNode::apply))
                .addNode("image_aggregator", node_async(imageAggregatorNode::apply))
                .addEdge(START, "image_plan")
                .addEdge("image_plan", "content_image_collector")
                .addEdge("image_plan", "illustration_collector")
                .addEdge("image_plan", "diagram_collector")
                .addEdge("image_plan", "logo_collector")
                .addEdge("content_image_collector", "image_aggregator")
                .addEdge("illustration_collector", "image_aggregator")
                .addEdge("diagram_collector", "image_aggregator")
                .addEdge("logo_collector", "image_aggregator")
                .addEdge("image_aggregator", END);
        return graph.compile();
    }

    public WorkflowContext execute(Long appId, String originalPrompt) throws Exception {
        WorkflowContext context = WorkflowContext.builder().appId(appId).originalPrompt(originalPrompt).build();
        var result = createWorkflow().invoke(context.toStateUpdate());
        if (result.isEmpty()) {
            throw new RuntimeException("Concurrent workflow returned empty result");
        }
        return WorkflowContext.fromState(result.get());
    }
}
