package com.adcage.acaicodefree.legacy.workflow.node;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.legacy.core.AiCodeGeneratorFacade;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.function.Consumer;

@Slf4j
public class CodeGeneratorNode {

    private final AiCodeGeneratorFacade aiCodeGeneratorFacade;
    private final Consumer<String> streamConsumer;

    public CodeGeneratorNode() {
        this(null);
    }

    public CodeGeneratorNode(AiCodeGeneratorFacade aiCodeGeneratorFacade) {
        this(aiCodeGeneratorFacade, null);
    }

    public CodeGeneratorNode(AiCodeGeneratorFacade aiCodeGeneratorFacade, Consumer<String> streamConsumer) {
        this.aiCodeGeneratorFacade = aiCodeGeneratorFacade;
        this.streamConsumer = streamConsumer;
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
        aiCodeGeneratorFacade.generateAndSaveCodeStream(prompt, generationType, ctx.getAppId())
                .doOnNext(chunk -> {
                    log.debug("[CodeGeneratorNode] chunk: {}", chunk);
                    if (streamConsumer != null) {
                        streamConsumer.accept(chunk);
                    }
                })
                .blockLast();
        log.info("[CodeGeneratorNode] stream completed");
        ctx.setGeneratedCodeDir(resolveGeneratedCodeDir(ctx.getAppId(), generationType));
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

    private String resolveGeneratedCodeDir(Long appId, CodeGenTypeEnum generationType) {
        return switch (generationType) {
            case VUE_PROJECT -> AppConstant.getVueProjectOutputDir(appId).toString();
            case MULTI_FILE -> AppConstant.getMultiFileOutputDir(appId).toString();
            case SINGLE_FILE -> AppConstant.getSingleFileOutputDir(appId).toString();
        };
    }
}
