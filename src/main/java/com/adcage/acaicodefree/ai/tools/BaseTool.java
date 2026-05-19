package com.adcage.acaicodefree.ai.tools;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;

public abstract class BaseTool {

    private static final Logger log = LoggerFactory.getLogger(BaseTool.class);

    protected Path codeOutputRootPath = AppConstant.getCodeOutputRootPath();

    public abstract String getToolName();

    public abstract String getDisplayName();

    public String generateToolRequestResponse(JSONObject arguments) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isNotBlank(relativePath)) {
            return "正在" + getDisplayName() + "：" + relativePath;
        }
        return "正在" + getDisplayName();
    }

    public String generateToolExecutedResult(JSONObject arguments, String result) {
        if (StrUtil.isNotBlank(result)) {
            return result;
        }
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isNotBlank(relativePath)) {
            return getDisplayName() + "完成：" + relativePath;
        }
        return getDisplayName() + "完成";
    }

    /**
     * 解析项目根目录（默认 Vue 工程）
     *
     * @param appId 应用 ID
     * @return 项目根目录路径
     */
    protected Path resolveProjectRoot(Long appId) {
        return resolveProjectRootByType(appId, CodeGenTypeEnum.VUE_PROJECT);
    }

    /**
     * 根据代码生成类型解析项目根目录
     *
     * @param appId       应用 ID
     * @param codeGenType 代码生成类型（支持 VUE_PROJECT, SINGLE_FILE, MULTI_FILE）
     * @return 项目根目录路径
     */
    protected Path resolveProjectRootByType(Long appId, CodeGenTypeEnum codeGenType) {
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
        return codeOutputRootPath.resolve(prefix + appId).normalize();
    }

    protected Path resolveRelativePath(String relativeFilePath, Long appId) {
        return resolveRelativePath(relativeFilePath, appId, CodeGenTypeEnum.VUE_PROJECT);
    }

    /**
     * 根据代码生成类型解析相对路径
     *
     * @param relativeFilePath 相对文件路径
     * @param appId            应用 ID
     * @param codeGenType      代码生成类型
     * @return 解析后的完整路径
     */
    protected Path resolveRelativePath(String relativeFilePath, Long appId, CodeGenTypeEnum codeGenType) {
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

    protected String toDisplayPath(Path path) {
        return path.toString().replace('\\', '/');
    }

    protected String extractRelativePath(JSONObject arguments) {
        if (arguments == null) {
            return "";
        }
        String relativeFilePath = arguments.getStr("relativeFilePath", "");
        if (StrUtil.isNotBlank(relativeFilePath)) {
            return relativeFilePath;
        }
        return arguments.getStr("relativeDirPath", "");
    }

    protected String summarizeText(String text, int maxLength) {
        if (StrUtil.isBlank(text)) {
            return "";
        }
        String normalized = text.replaceAll("\\s+", " ").trim();
        if (normalized.length() <= maxLength) {
            return normalized;
        }
        return normalized.substring(0, maxLength) + "...";
    }

    protected long logToolStart(String action, Long appId, CodeGenTypeEnum codeGenType, String targetPath) {
        long startNanos = System.nanoTime();
        log.info("工具开始执行, tool={}, action={}, appId={}, codeGenType={}, path={}",
                getToolName(), action, appId, codeGenType == null ? "unknown" : codeGenType.name(), targetPath);
        return startNanos;
    }

    protected void logToolSuccess(String action, Long appId, CodeGenTypeEnum codeGenType,
                                  String targetPath, long startNanos) {
        long costMs = (System.nanoTime() - startNanos) / 1_000_000;
        log.info("工具执行成功, tool={}, action={}, appId={}, codeGenType={}, path={}, costMs={}",
                getToolName(), action, appId, codeGenType == null ? "unknown" : codeGenType.name(), targetPath, costMs);
    }

    protected void logToolFailure(String action, Long appId, CodeGenTypeEnum codeGenType,
                                  String targetPath, long startNanos, Exception e) {
        long costMs = (System.nanoTime() - startNanos) / 1_000_000;
        log.error("工具执行失败, tool={}, action={}, appId={}, codeGenType={}, path={}, costMs={}",
                getToolName(), action, appId, codeGenType == null ? "unknown" : codeGenType.name(), targetPath, costMs, e);
    }
}
