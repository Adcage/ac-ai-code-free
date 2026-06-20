package com.adcage.acaicodefree.legacy.workflow.node;

import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Map;

@Slf4j
public class ProjectBuilderNode {

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        log.info("[ProjectBuilderNode] starting, generatedCodeDir={}", ctx.getGeneratedCodeDir());
        ctx.advanceStep("project_builder");
        ctx.setBuildResultDir("[stub] /build/" + ctx.getAppId());
        log.info("[ProjectBuilderNode] completed, buildResultDir={}", ctx.getBuildResultDir());
        return ctx.toStateUpdate();
    }
}
