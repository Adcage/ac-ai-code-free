package com.adcage.acaicodefree.workflow.node;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Map;

@Slf4j
public class RouterNode {

    public static final String ROUTE_SINGLE = "single_file";
    public static final String ROUTE_MULTI = "multi_file";

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        log.info("[RouterNode] starting, enhancedPrompt length={}", ctx.getEnhancedPrompt().length());
        ctx.advanceStep("router");
        String prompt = ctx.getEnhancedPrompt() != null ? ctx.getEnhancedPrompt().toLowerCase() : "";
        CodeGenTypeEnum type = prompt.contains("首页") || prompt.contains("官网") || prompt.contains("多页面")
                ? CodeGenTypeEnum.MULTI_FILE
                : CodeGenTypeEnum.SINGLE_FILE;
        ctx.setGenerationType(type);
        log.info("[RouterNode] completed, generationType={}", type);
        return ctx.toStateUpdate();
    }
}
