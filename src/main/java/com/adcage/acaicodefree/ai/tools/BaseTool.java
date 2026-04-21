package com.adcage.acaicodefree.ai.tools;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.exception.BusinessException;

import java.nio.file.Path;

public abstract class BaseTool {

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

    protected Path resolveProjectRoot(Long appId) {
        if (appId == null || appId <= 0) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用 ID 非法");
        }
        return codeOutputRootPath.resolve(AppConstant.VUE_PROJECT_OUTPUT_PREFIX + appId).normalize();
    }

    protected Path resolveRelativePath(String relativeFilePath, Long appId) {
        if (StrUtil.isBlank(relativeFilePath)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "文件路径不能为空");
        }
        Path relativePath = Path.of(relativeFilePath.trim());
        if (relativePath.isAbsolute()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "非法文件路径");
        }
        Path projectRoot = resolveProjectRoot(appId);
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
}
