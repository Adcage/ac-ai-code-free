package com.adcage.acaicodefree.ai.tools;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.ToolMemoryId;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;

@Component
public class FileDirReadTool extends BaseTool {

    private static final int MAX_DEPTH = 6;

    private static final int MAX_ENTRIES_PER_DIR = 200;

    @Override
    public String getToolName() {
        return "readDir";
    }

    @Override
    public String getDisplayName() {
        return "读目录";
    }

    @Override
    public String generateToolRequestResponse(JSONObject arguments) {
        String relativeDirPath = extractRelativePath(arguments);
        if (StrUtil.isBlank(relativeDirPath)) {
            return "准备读取目录结构";
        }
        return "准备读取目录结构 " + relativeDirPath;
    }

    @Override
    public String generateToolExecutedResult(JSONObject arguments, String result) {
        String relativeDirPath = extractRelativePath(arguments);
        if (StrUtil.isBlank(relativeDirPath)) {
            return "目录结构读取完成";
        }
        return "目录结构读取完成 " + relativeDirPath;
    }

    @Tool("读取目录结构")
    public String readDir(String relativeDirPath, @ToolMemoryId Long appId) {
        Path projectRoot = resolveProjectRoot(appId);
        Path targetDir;
        if (StrUtil.isBlank(relativeDirPath)) {
            targetDir = projectRoot;
        } else {
            targetDir = resolveRelativePath(relativeDirPath, appId);
        }
        if (!Files.exists(targetDir) || !Files.isDirectory(targetDir)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "目录不存在");
        }
        StringBuilder builder = new StringBuilder();
        appendDirectory(builder, targetDir, projectRoot, 0);
        return builder.toString().trim();
    }

    private void appendDirectory(StringBuilder builder, Path current, Path projectRoot, int depth) {
        if (depth > MAX_DEPTH) {
            appendLine(builder, depth, "... (目录层级已截断)");
            return;
        }
        String displayName = projectRoot.equals(current)
                ? "."
                : toDisplayPath(projectRoot.relativize(current));
        appendLine(builder, depth, displayName + "/");
        try {
            List<Path> children;
            try (Stream<Path> pathStream = Files.list(current)) {
                children = pathStream
                        .sorted(Comparator.comparing(Path::getFileName))
                        .toList();
            }
            int count = 0;
            for (Path child : children) {
                count++;
                if (count > MAX_ENTRIES_PER_DIR) {
                    appendLine(builder, depth + 1, "... (目录项过多，已截断)");
                    break;
                }
                if (Files.isDirectory(child)) {
                    appendDirectory(builder, child, projectRoot, depth + 1);
                } else {
                    appendLine(builder, depth + 1, child.getFileName().toString());
                }
            }
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "读取目录失败");
        }
    }

    private void appendLine(StringBuilder builder, int depth, String text) {
        builder.append("  ".repeat(Math.max(0, depth))).append(text).append('\n');
    }
}
