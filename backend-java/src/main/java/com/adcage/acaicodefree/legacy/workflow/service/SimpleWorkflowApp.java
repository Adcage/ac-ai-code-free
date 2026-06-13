package com.adcage.acaicodefree.legacy.workflow.service;

import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.CompiledGraph;
import org.bsc.langgraph4j.StateGraph;
import org.bsc.langgraph4j.state.AgentState;
import org.bsc.langgraph4j.state.Channel;
import org.bsc.langgraph4j.state.Channels;

import java.util.Map;

import static org.bsc.langgraph4j.action.AsyncNodeAction.node_async;
import static org.bsc.langgraph4j.StateGraph.END;
import static org.bsc.langgraph4j.StateGraph.START;

@Slf4j
public class SimpleWorkflowApp {

    public static final Map<String, Channel<?>> SCHEMA = Map.of(
            "currentStep", Channels.base(() -> ""),
            "message", Channels.base(() -> "")
    );

    public CompiledGraph<AgentState> createWorkflow() throws Exception {
        var graph = new StateGraph<>(SCHEMA, AgentState::new)
                .addNode("step_one", node_async(this::stepOne))
                .addNode("step_two", node_async(this::stepTwo))
                .addEdge(START, "step_one")
                .addEdge("step_one", "step_two")
                .addEdge("step_two", END);

        return graph.compile();
    }

    private Map<String, Object> stepOne(AgentState state) {
        log.info("[SimpleWorkflow] step_one executing");
        return Map.of(
                "currentStep", "step_one",
                "message", "Step one completed"
        );
    }

    private Map<String, Object> stepTwo(AgentState state) {
        log.info("[SimpleWorkflow] step_two executing, previous step: {}", state.value("currentStep").orElse(""));
        return Map.of(
                "currentStep", "step_two",
                "message", "Step two completed"
        );
    }
}
