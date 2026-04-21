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
import java.util.Set;

@Component
public class FileDeleteTool extends BaseTool {

    private static final Set<String> PROTECTED_ROOT_FILES = Set.of(
            "package.json",
            "vite.config.js",
            "vite.config.ts",
            "vue.config.js",
            "tsconfig.json",
            "readme.md",
            ".gitignore",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "bun.lockb"
    );

    private static final Set<String> PROTECTED_PROJECT_FILES = Set.of(
            "src/main.js",
            "src/main.ts",
            "src/app.vue"
    );

    @Override
    public String getToolName() {
        return "deleteFile";
    }

    @Override
    public String getDisplayName() {
        return "删文件";
    }

    @Override
    public String generateToolRequestResponse(JSONObject arguments) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isBlank(relativePath)) {
            return "准备删除文件";
        }
        return "准备删除文件 " + relativePath;
    }

    @Override
    public String generateToolExecutedResult(JSONObject arguments, String result) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isNotBlank(relativePath) && StrUtil.isNotBlank(result) && result.startsWith("文件删除成功")) {
            return "已删除文件 " + relativePath;
        }
        return StrUtil.blankToDefault(result, "文件删除完成");
    }

    @Tool("删除指定文件，自动保护关键文件")
    public String deleteFile(String relativeFilePath, @ToolMemoryId Long appId) {
        Path normalized = resolveRelativePath(relativeFilePath, appId);
        Path projectRoot = resolveProjectRoot(appId);
        Path relativePath = projectRoot.relativize(normalized);
        String displayRelativePath = toDisplayPath(relativePath);
        String normalizedRelativePath = displayRelativePath.toLowerCase();
        if (isProtectedFile(normalizedRelativePath)) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR, "禁止删除关键文件：" + displayRelativePath);
        }
        if (!Files.exists(normalized) || !Files.isRegularFile(normalized)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "文件不存在");
        }
        try {
            Files.delete(normalized);
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件删除失败");
        }
        return "文件删除成功：" + displayRelativePath;
    }

    private boolean isProtectedFile(String normalizedRelativePath) {
        if (PROTECTED_PROJECT_FILES.contains(normalizedRelativePath)) {
            return true;
        }
        String fileName = Path.of(normalizedRelativePath).getFileName().toString().toLowerCase();
        return PROTECTED_ROOT_FILES.contains(normalizedRelativePath) || PROTECTED_ROOT_FILES.contains(fileName);
    }
}
