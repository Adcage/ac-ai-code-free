package com.adcage.acaicodefree.service;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import jakarta.annotation.Resource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

@Service
public class FileOperationService {

    private static final Logger log = LoggerFactory.getLogger(FileOperationService.class);

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

    private static final int MAX_DEPTH = 6;
    private static final int MAX_ENTRIES_PER_DIR = 200;

    private final Path codeOutputRootPath = AppConstant.getCodeOutputRootPath();

    public String readFile(Long appId, String codeGenType, String relativeFilePath) {
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path normalized = resolveRelativePath(relativeFilePath, appId, genType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        String displayPath = toDisplayPath(projectRoot.relativize(normalized));
        long startNanos = logToolStart("readFile", appId, genType, displayPath);
        if (!Files.exists(normalized) || !Files.isRegularFile(normalized)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "文件不存在");
        }
        try {
            String content = Files.readString(normalized, StandardCharsets.UTF_8);
            logToolSuccess("readFile", appId, genType, displayPath, startNanos);
            return content;
        } catch (IOException e) {
            logToolFailure("readFile", appId, genType, displayPath, startNanos, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件读取失败");
        }
    }

    public String writeFile(Long appId, String codeGenType, String relativeFilePath, String content) {
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path normalized = resolveRelativePath(relativeFilePath, appId, genType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        String displayPath = toDisplayPath(projectRoot.relativize(normalized));
        long startNanos = logToolStart("writeFile", appId, genType, displayPath);
        try {
            Path parent = normalized.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(normalized, content == null ? "" : content, StandardCharsets.UTF_8);
            logToolSuccess("writeFile", appId, genType, displayPath, startNanos);
        } catch (IOException e) {
            logToolFailure("writeFile", appId, genType, displayPath, startNanos, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件写入失败");
        }
        return "文件写入成功：" + displayPath;
    }

    public String modifyFile(Long appId, String codeGenType, String relativeFilePath,
                             String oldContent, String newContent) {
        if (StrUtil.isBlank(oldContent)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "oldContent 不能为空");
        }
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path normalized = resolveRelativePath(relativeFilePath, appId, genType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        String displayPath = toDisplayPath(projectRoot.relativize(normalized));
        long startNanos = logToolStart("modifyFile", appId, genType, displayPath);
        if (!Files.exists(normalized) || !Files.isRegularFile(normalized)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "文件不存在");
        }
        try {
            String original = Files.readString(normalized, StandardCharsets.UTF_8);
            if (!original.contains(oldContent)) {
                logToolSuccess("modifyFile-noop", appId, genType, displayPath, startNanos);
                return "文件修改失败：未找到匹配内容 " + toDisplayPath(projectRoot.relativize(normalized));
            }
            String replaced = original.replace(oldContent, StrUtil.nullToEmpty(newContent));
            Files.writeString(normalized, replaced, StandardCharsets.UTF_8);
            logToolSuccess("modifyFile", appId, genType, displayPath, startNanos);
            return "文件修改成功：" + displayPath;
        } catch (IOException e) {
            logToolFailure("modifyFile", appId, genType, displayPath, startNanos, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件修改失败");
        }
    }

    public String deleteFile(Long appId, String codeGenType, String relativeFilePath) {
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path normalized = resolveRelativePath(relativeFilePath, appId, genType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        Path relativePath = projectRoot.relativize(normalized);
        String displayRelativePath = toDisplayPath(relativePath);
        long startNanos = logToolStart("deleteFile", appId, genType, displayRelativePath);
        String normalizedRelativePath = displayRelativePath.toLowerCase();
        if (isProtectedFile(normalizedRelativePath)) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR, "禁止删除关键文件：" + displayRelativePath);
        }
        if (!Files.exists(normalized) || !Files.isRegularFile(normalized)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "文件不存在");
        }
        try {
            Files.delete(normalized);
            logToolSuccess("deleteFile", appId, genType, displayRelativePath, startNanos);
        } catch (IOException e) {
            logToolFailure("deleteFile", appId, genType, displayRelativePath, startNanos, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件删除失败");
        }
        return "文件删除成功：" + displayRelativePath;
    }

    public String readDir(Long appId, String codeGenType, String relativeDirPath) {
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        Path targetDir;
        if (StrUtil.isBlank(relativeDirPath)) {
            targetDir = projectRoot;
        } else {
            targetDir = resolveRelativePath(relativeDirPath, appId, genType);
        }
        String displayPath = projectRoot.equals(targetDir) ? "." : toDisplayPath(projectRoot.relativize(targetDir));
        long startNanos = logToolStart("readDir", appId, genType, displayPath);
        if (!Files.exists(targetDir) || !Files.isDirectory(targetDir)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "目录不存在");
        }
        StringBuilder builder = new StringBuilder();
        appendDirectory(builder, targetDir, projectRoot, 0);
        logToolSuccess("readDir", appId, genType, displayPath, startNanos);
        return builder.toString().trim();
    }

    public String generateToolRequestResponse(String toolName, JSONObject arguments) {
        String relativePath = extractRelativePath(arguments);
        String displayName = getDisplayName(toolName);
        if (StrUtil.isNotBlank(relativePath)) {
            return "准备" + displayName + " " + relativePath;
        }
        return "准备" + displayName;
    }

    public String generateToolExecutedResult(String toolName, JSONObject arguments, String result) {
        String relativePath = extractRelativePath(arguments);
        String displayName = getDisplayName(toolName);
        if (StrUtil.isNotBlank(result) && result.startsWith("文件修改失败")) {
            return firstLine(result);
        }
        if (StrUtil.isNotBlank(relativePath)) {
            return "已" + displayName + " " + relativePath;
        }
        if (StrUtil.isNotBlank(result) && result.startsWith("文件删除成功")) {
            String path = extractRelativePath(arguments);
            return StrUtil.isNotBlank(path) ? "已删除文件 " + path : firstLine(result);
        }
        if (StrUtil.isNotBlank(result) && result.startsWith("文件写入成功")) {
            String path = extractRelativePath(arguments);
            return StrUtil.isNotBlank(path) ? "已写入文件 " + path : firstLine(result);
        }
        // 兜底：绝不返回原始 result。read_file 的文件内容、run_checks 的多行校验结果
        // 都会走到这里（无 relativePath），若原样返回会以 `[工具完成] <多行>` 追加进持久化消息，
        // 刷新时按行解析会把后续行泄漏进对话气泡。统一返回单行摘要，与前端流式展示一致。
        return StrUtil.isBlank(toolName) ? "工具执行完成" : "已执行 " + toolName;
    }

    private String firstLine(String text) {
        if (StrUtil.isBlank(text)) {
            return text;
        }
        int idx = text.indexOf('\n');
        return idx >= 0 ? text.substring(0, idx) : text;
    }

    private String getDisplayName(String toolName) {
        if (StrUtil.isBlank(toolName)) {
            return "处理";
        }
        return switch (toolName) {
            case "readFile" -> "读取文件";
            case "writeFile" -> "写入文件";
            case "modifyFile" -> "修改文件";
            case "deleteFile" -> "删除文件";
            case "readDir" -> "读取目录结构";
            default -> "处理";
        };
    }

    private Path resolveProjectRootByType(Long appId, CodeGenTypeEnum codeGenType) {
        if (appId == null || appId <= 0) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用 ID 非法");
        }
        if (codeGenType == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "代码生成类型不能为空");
        }
        String prefix = switch (codeGenType) {
            case SINGLE_FILE -> AppConstant.SINGLE_FILE_OUTPUT_PREFIX;
            case MULTI_FILE -> AppConstant.MULTI_FILE_OUTPUT_PREFIX;
            case VUE_PROJECT -> AppConstant.VUE_PROJECT_OUTPUT_PREFIX;
        };
        return codeOutputRootPath.resolve(prefix).resolve(String.valueOf(appId)).normalize();
    }

    private Path resolveRelativePath(String relativeFilePath, Long appId, CodeGenTypeEnum codeGenType) {
        if (StrUtil.isBlank(relativeFilePath)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "文件路径不能为空");
        }
        Path relativePath = Path.of(relativeFilePath.trim());
        if (relativePath.isAbsolute()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "非法文件路径");
        }
        Path projectRoot = resolveProjectRootByType(appId, codeGenType);
        Path normalized = projectRoot.resolve(relativePath).normalize();
        if (!normalized.startsWith(projectRoot)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "非法文件路径");
        }
        return normalized;
    }

    private String toDisplayPath(Path path) {
        return path.toString().replace('\\', '/');
    }

    private String extractRelativePath(JSONObject arguments) {
        if (arguments == null) {
            return "";
        }
        String relativeFilePath = arguments.getStr("relativeFilePath", "");
        if (StrUtil.isNotBlank(relativeFilePath)) {
            return relativeFilePath;
        }
        return arguments.getStr("relativeDirPath", "");
    }

    private boolean isProtectedFile(String normalizedRelativePath) {
        if (PROTECTED_PROJECT_FILES.contains(normalizedRelativePath)) {
            return true;
        }
        String fileName = Path.of(normalizedRelativePath).getFileName().toString().toLowerCase();
        return PROTECTED_ROOT_FILES.contains(normalizedRelativePath) || PROTECTED_ROOT_FILES.contains(fileName);
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

    private CodeGenTypeEnum parseCodeGenType(String codeGenType) {
        if (StrUtil.isBlank(codeGenType)) {
            return CodeGenTypeEnum.VUE_PROJECT;
        }
        CodeGenTypeEnum type = CodeGenTypeEnum.getEnumByValue(codeGenType);
        return type != null ? type : CodeGenTypeEnum.VUE_PROJECT;
    }

    private long logToolStart(String action, Long appId, CodeGenTypeEnum codeGenType, String targetPath) {
        long startNanos = System.nanoTime();
        log.info("工具开始执行, action={}, appId={}, codeGenType={}, path={}",
                action, appId, codeGenType == null ? "unknown" : codeGenType.name(), targetPath);
        return startNanos;
    }

    private void logToolSuccess(String action, Long appId, CodeGenTypeEnum codeGenType,
                                String targetPath, long startNanos) {
        long costMs = (System.nanoTime() - startNanos) / 1_000_000;
        log.info("工具执行成功, action={}, appId={}, codeGenType={}, path={}, costMs={}",
                action, appId, codeGenType == null ? "unknown" : codeGenType.name(), targetPath, costMs);
    }

    private void logToolFailure(String action, Long appId, CodeGenTypeEnum codeGenType,
                                String targetPath, long startNanos, Exception e) {
        long costMs = (System.nanoTime() - startNanos) / 1_000_000;
        log.error("工具执行失败, action={}, appId={}, codeGenType={}, path={}, costMs={}",
                action, appId, codeGenType == null ? "unknown" : codeGenType.name(), targetPath, costMs, e);
    }
}
