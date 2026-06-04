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
public class FileWriteTool extends BaseTool {

    @Override
    public String getToolName() {
        return "writeFile";
    }

    @Override
    public String getDisplayName() {
        return "写文件";
    }

    @Override
    public String generateToolRequestResponse(JSONObject arguments) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isBlank(relativePath)) {
            return "准备写入文件";
        }
        return "准备写入文件 " + relativePath;
    }

    @Override
    public String generateToolExecutedResult(JSONObject arguments, String result) {
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isNotBlank(relativePath)) {
            return "已写入文件 " + relativePath;
        }
        return StrUtil.blankToDefault(result, "文件写入成功");
    }

    @Tool("写入文件到指定路径")
    public String writeFile(String relativeFilePath, String content, @ToolMemoryId Long appId, String codeGenType) {
        CodeGenTypeEnum genType = parseCodeGenType(codeGenType);
        Path normalized = resolveRelativePath(relativeFilePath, appId, genType);
        Path projectRoot = resolveProjectRootByType(appId, genType);
        String displayPath = toDisplayPath(projectRoot.relativize(normalized));
        long startNanos = logToolStart("write", appId, genType, displayPath);
        try {
            Path parent = normalized.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(normalized, content == null ? "" : content, StandardCharsets.UTF_8);
            logToolSuccess("write", appId, genType, displayPath, startNanos);
        } catch (IOException e) {
            logToolFailure("write", appId, genType, displayPath, startNanos, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件写入失败");
        }
        return "文件写入成功：" + displayPath;
    }

    private CodeGenTypeEnum parseCodeGenType(String codeGenType) {
        if (StrUtil.isBlank(codeGenType)) {
            return CodeGenTypeEnum.VUE_PROJECT;
        }
        CodeGenTypeEnum type = CodeGenTypeEnum.getEnumByValue(codeGenType);
        return type != null ? type : CodeGenTypeEnum.VUE_PROJECT;
    }
}
