package com.adcage.acaicodefree.legacy.workflow.node;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.legacy.workflow.model.QualityResult;
import com.adcage.acaicodefree.legacy.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

@Slf4j
public class CodeQualityCheckNode {

    public static final String ROUTE_RETRY = "retry";
    public static final String ROUTE_SKIP_BUILD = "skip_build";
    public static final String ROUTE_BUILD = "build";

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        log.info("[CodeQualityCheckNode] starting, generatedCodeDir={}", ctx.getGeneratedCodeDir());
        ctx.advanceStep("code_quality_check");
        ctx.setQualityResult(checkGeneratedResult(ctx));
        log.info("[CodeQualityCheckNode] completed, isValid={}", ctx.getQualityResult().getIsValid());
        return ctx.toStateUpdate();
    }

    public String routeAfterCheck(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        if (ctx.getQualityResult() == null || !ctx.getQualityResult().getIsValid()) {
            log.info("[CodeQualityCheckNode] routing to retry");
            return ROUTE_RETRY;
        }
        log.info("[CodeQualityCheckNode] routing to skip_build (no build needed for current modes)");
        return ROUTE_SKIP_BUILD;
    }

    private QualityResult checkGeneratedResult(WorkflowContext ctx) {
        List<String> errors = new ArrayList<>();
        String generatedCodeDir = ctx.getGeneratedCodeDir();
        if (StrUtil.isBlank(generatedCodeDir)) {
            errors.add("generatedCodeDir 为空");
            return QualityResult.invalid(errors);
        }
        Path dir = Path.of(generatedCodeDir);
        if (!Files.isDirectory(dir)) {
            errors.add("生成目录不存在: " + generatedCodeDir);
            return QualityResult.invalid(errors);
        }
        boolean hasHtml = containsFileWithSuffix(dir, ".html");
        if (!hasHtml) {
            errors.add("缺少 html 文件");
        }
        if (ctx.getGenerationType() != CodeGenTypeEnum.MULTI_FILE) {
            if (!errors.isEmpty()) {
                return QualityResult.invalid(errors);
            }
            return QualityResult.valid();
        }
        boolean hasStyle = Files.exists(dir.resolve("style.css"));
        boolean hasScript = Files.exists(dir.resolve("script.js"));
        if (!Files.exists(dir.resolve("index.html"))) {
            errors.add("缺少 index.html");
        }
        if (hasHtml && (!hasStyle || !hasScript)) {
            if (!hasStyle) {
                errors.add("缺少 style.css");
            }
            if (!hasScript) {
                errors.add("缺少 script.js");
            }
        }
        if (!errors.isEmpty()) {
            return QualityResult.invalid(errors);
        }
        return QualityResult.valid();
    }

    private boolean containsFileWithSuffix(Path dir, String suffix) {
        try (Stream<Path> stream = Files.list(dir)) {
            return stream.anyMatch(path -> Files.isRegularFile(path) && path.getFileName().toString().endsWith(suffix));
        } catch (IOException e) {
            log.warn("[CodeQualityCheckNode] failed to inspect generated dir={}", dir, e);
            return false;
        }
    }
}
