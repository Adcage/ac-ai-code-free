package com.adcage.acaicodefree.ai.tools;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.ToolMemoryId;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

@Component
public class FileReadTool extends BaseTool {

    @Override
    public String getToolName() {
        return "readFile";
    }

    @Override
    public String getDisplayName() {
        return "读文件";
    }

    @Override
    public String generateToolRequestResponse(JSONObject arguments) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isBlank(relativePath)) {
            return "准备读取文件";
        }
        return "准备读取文件 " + relativePath;
    }

    @Override
    public String generateToolExecutedResult(JSONObject arguments, String result) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isNotBlank(relativePath)) {
            return "已读取文件 " + relativePath;
        }
        return "文件读取完成";
    }

    @Tool("读取指定文件内容")
    public String readFile(String relativeFilePath, @ToolMemoryId Long appId, String codeGenType) {
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path normalized = resolveRelativePath(relativeFilePath, appId, genType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        String displayPath = toDisplayPath(projectRoot.relativize(normalized));
        long startNanos = logToolStart("read", appId, genType, displayPath);
        if (!Files.exists(normalized) || !Files.isRegularFile(normalized)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "文件不存在");
        }
        try {
            String content = Files.readString(normalized, StandardCharsets.UTF_8);
            logToolSuccess("read", appId, genType, displayPath, startNanos);
            return content;
        } catch (IOException e) {
            logToolFailure("read", appId, genType, displayPath, startNanos, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件读取失败");
        }
    }

    private CodeGenTypeEnum parseCodeGenType(String codeGenType) {
        if (StrUtil.isBlank(codeGenType)) {
            return CodeGenTypeEnum.VUE_PROJECT;
        }
        CodeGenTypeEnum type = CodeGenTypeEnum.getEnumByValue(codeGenType);
        return type != null ? type : CodeGenTypeEnum.VUE_PROJECT;
    }
}
