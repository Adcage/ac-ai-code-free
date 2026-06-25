package com.adcage.acaicodefree.legacy.workflow.node;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.util.Map;

@Slf4j
@Deprecated
public class RouterNode {

    public static final String ROUTE_SINGLE = "single_file";
    public static final String ROUTE_MULTI = "multi_file";

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        log.info("[RouterNode] starting, enhancedPrompt length={}", ctx.getEnhancedPrompt().length());
        ctx.advanceStep("router");
        String prompt = ctx.getEnhancedPrompt() != null ? ctx.getEnhancedPrompt().toLowerCase() : "";
        CodeGenTypeEnum type;
        if (isVueProjectPrompt(prompt)) {
            type = CodeGenTypeEnum.VUE_PROJECT;
        } else if (prompt.contains("首页") || prompt.contains("官网") || prompt.contains("多页面")) {
            type = CodeGenTypeEnum.MULTI_FILE;
        } else {
            type = CodeGenTypeEnum.SINGLE_FILE;
        }
        ctx.setGenerationType(type);
        log.info("[RouterNode] completed, generationType={}", type);
        return ctx.toStateUpdate();
    }

    private boolean isVueProjectPrompt(String prompt) {
        return prompt.contains("vue")
                || prompt.contains("组件")
                || prompt.contains("spa")
                || prompt.contains("单页应用")
                || prompt.contains("管理系统")
                || prompt.contains("后台管理")
                || prompt.contains("dashboard")
                || prompt.contains("admin");
    }
}
