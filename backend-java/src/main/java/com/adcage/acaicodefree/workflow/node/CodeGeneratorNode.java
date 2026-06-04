package com.adcage.acaicodefree.workflow.node;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.core.AiCodeGeneratorFacade;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

@Slf4j
public class CodeGeneratorNode {

    private final AiCodeGeneratorFacade aiCodeGeneratorFacade;

    public CodeGeneratorNode() {
        this(null);
    }

    public CodeGeneratorNode(AiCodeGeneratorFacade aiCodeGeneratorFacade) {
        this.aiCodeGeneratorFacade = aiCodeGeneratorFacade;
    }

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        log.info("[CodeGeneratorNode] starting, generationType={}, enhancedPrompt length={}",
                ctx.getGenerationType(), ctx.getEnhancedPrompt() != null ? ctx.getEnhancedPrompt().length() : 0);
        ctx.advanceStep("code_generator");
        CodeGenTypeEnum generationType = ctx.getGenerationType() == null ? CodeGenTypeEnum.MULTI_FILE : ctx.getGenerationType();
        ctx.setGenerationType(generationType);
        if (aiCodeGeneratorFacade == null) {
            ctx.setGeneratedCodeDir(createStubGeneratedDir(ctx.getAppId(), generationType));
            log.info("[CodeGeneratorNode] facade unavailable, fallback to stub directory={}", ctx.getGeneratedCodeDir());
            return ctx.toStateUpdate();
        }
        String prompt = StrUtil.blankToDefault(ctx.getEnhancedPrompt(), ctx.getOriginalPrompt());
        File generatedFile = aiCodeGeneratorFacade.generateAndSaveCode(prompt, generationType, ctx.getAppId());
        ctx.setGeneratedCodeDir(generatedFile.getAbsolutePath());
        log.info("[CodeGeneratorNode] completed, generatedCodeDir={}", ctx.getGeneratedCodeDir());
        return ctx.toStateUpdate();
    }

    private String createStubGeneratedDir(Long appId, CodeGenTypeEnum generationType) {
        try {
            Path dir = Files.createTempDirectory("workflow-generated-" + appId + "-");
            Files.writeString(dir.resolve("index.html"), "<html><body>stub</body></html>");
            if (generationType == CodeGenTypeEnum.MULTI_FILE) {
                Files.writeString(dir.resolve("style.css"), "body { font-family: sans-serif; }");
                Files.writeString(dir.resolve("script.js"), "console.log('stub')");
            }
            return dir.toAbsolutePath().toString();
        } catch (IOException e) {
            throw new RuntimeException("创建工作流临时代码目录失败", e);
        }
    }
}
