package com.adcage.acaicodefree.legacy.workflow.service;

import com.adcage.acaicodefree.legacy.workflow.node.*;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.CompiledGraph;
import org.bsc.langgraph4j.StateGraph;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Map;

import static org.bsc.langgraph4j.StateGraph.END;
import static org.bsc.langgraph4j.StateGraph.START;
import static org.bsc.langgraph4j.action.AsyncEdgeAction.edge_async;
import static org.bsc.langgraph4j.action.AsyncNodeAction.node_async;

@Slf4j
@Deprecated
public class CodeGenWorkflow {

    public static final String NODE_IMAGE_COLLECT = "image_collect";
    public static final String NODE_PROMPT_ENHANCER = "prompt_enhancer";
    public static final String NODE_ROUTER = "router";
    public static final String NODE_CODE_GENERATOR = "code_generator";
    public static final String NODE_CODE_QUALITY_CHECK = "code_quality_check";
    public static final String NODE_PROJECT_BUILDER = "project_builder";

    private final ImageCollectorNode imageCollectorNode;
    private final PromptEnhancerNode promptEnhancerNode;
    private final RouterNode routerNode;
    private final CodeGeneratorNode codeGeneratorNode;
    private final CodeQualityCheckNode codeQualityCheckNode;
    private final ProjectBuilderNode projectBuilderNode;

    public CodeGenWorkflow() {
        this(new ImageCollectorNode(), new PromptEnhancerNode(), new RouterNode(),
                new CodeGeneratorNode(), new CodeQualityCheckNode(), new ProjectBuilderNode());
    }

    public CodeGenWorkflow(ImageCollectorNode imageCollectorNode,
                           PromptEnhancerNode promptEnhancerNode,
                           RouterNode routerNode,
                           CodeGeneratorNode codeGeneratorNode,
                           CodeQualityCheckNode codeQualityCheckNode,
                           ProjectBuilderNode projectBuilderNode) {
        this.imageCollectorNode = imageCollectorNode;
        this.promptEnhancerNode = promptEnhancerNode;
        this.routerNode = routerNode;
        this.codeGeneratorNode = codeGeneratorNode;
        this.codeQualityCheckNode = codeQualityCheckNode;
        this.projectBuilderNode = projectBuilderNode;
    }

    public CompiledGraph<AgentState> createWorkflow() throws Exception {
        var schema = WorkflowContext.schema();

        var graph = new StateGraph<>(schema, AgentState::new)
                .addNode(NODE_IMAGE_COLLECT, node_async(imageCollectorNode::apply))
                .addNode(NODE_PROMPT_ENHANCER, node_async(promptEnhancerNode::apply))
                .addNode(NODE_ROUTER, node_async(routerNode::apply))
                .addNode(NODE_CODE_GENERATOR, node_async(codeGeneratorNode::apply))
                .addNode(NODE_CODE_QUALITY_CHECK, node_async(codeQualityCheckNode::apply))
                .addNode(NODE_PROJECT_BUILDER, node_async(projectBuilderNode::apply))
                .addEdge(START, NODE_IMAGE_COLLECT)
                .addEdge(NODE_IMAGE_COLLECT, NODE_PROMPT_ENHANCER)
                .addEdge(NODE_PROMPT_ENHANCER, NODE_ROUTER)
                .addEdge(NODE_ROUTER, NODE_CODE_GENERATOR)
                .addEdge(NODE_CODE_GENERATOR, NODE_CODE_QUALITY_CHECK)
                .addConditionalEdges(NODE_CODE_QUALITY_CHECK,
                        edge_async(codeQualityCheckNode::routeAfterCheck),
                        Map.of(
                                CodeQualityCheckNode.ROUTE_RETRY, NODE_CODE_GENERATOR,
                                CodeQualityCheckNode.ROUTE_SKIP_BUILD, END,
                                CodeQualityCheckNode.ROUTE_BUILD, NODE_PROJECT_BUILDER
                        ))
                .addEdge(NODE_PROJECT_BUILDER, END);

        return graph.compile();
    }

    public WorkflowContext execute(Long appId, String originalPrompt) throws Exception {
        CompiledGraph<AgentState> workflow = createWorkflow();

        var initialContext = WorkflowContext.builder()
                .appId(appId)
                .originalPrompt(originalPrompt)
                .build();

        var result = workflow.invoke(initialContext.toStateUpdate());
        if (result.isEmpty()) {
            throw new RuntimeException("Workflow execution returned empty result");
        }
        return WorkflowContext.fromState(result.get());
    }
}
