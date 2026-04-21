package com.adcage.acaicodefree.ai.tools;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.ToolMemoryId;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

@Component
public class FileModifyTool extends BaseTool {

    @Override
    public String getToolName() {
        return "modifyFile";
    }

    @Override
    public String getDisplayName() {
        return "改文件";
    }

    @Override
    public String generateToolRequestResponse(JSONObject arguments) {
        String relativePath = extractRelativePath(arguments);
        String oldContent = summarizeText(arguments == null ? "" : arguments.getStr("oldContent", ""), 40);
        String newContent = summarizeText(arguments == null ? "" : arguments.getStr("newContent", ""), 40);
        if (StrUtil.isBlank(relativePath)) {
            return "准备修改文件";
        }
        if (StrUtil.isBlank(oldContent) && StrUtil.isBlank(newContent)) {
            return "准备修改文件 " + relativePath;
        }
        return "准备修改文件 " + relativePath + "（替换：" + oldContent + " -> " + newContent + "）";
    }

    @Override
    public String generateToolExecutedResult(JSONObject arguments, String result) {
        if (StrUtil.isNotBlank(result) && result.startsWith("文件修改失败")) {
            return result;
        }
        String relativePath = extractRelativePath(arguments);
        if (StrUtil.isNotBlank(relativePath)) {
            return "已修改文件 " + relativePath;
        }
        return StrUtil.blankToDefault(result, "文件修改完成");
    }

    @Tool("替换文件中的指定内容")
    public String modifyFile(String relativeFilePath, String oldContent, String newContent, @ToolMemoryId Long appId) {
        if (StrUtil.isBlank(oldContent)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "oldContent 不能为空");
        }
        Path normalized = resolveRelativePath(relativeFilePath, appId);
        Path projectRoot = resolveProjectRoot(appId);
        if (!Files.exists(normalized) || !Files.isRegularFile(normalized)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "文件不存在");
        }
        try {
            String original = Files.readString(normalized, StandardCharsets.UTF_8);
            if (!original.contains(oldContent)) {
                return "文件修改失败：未找到匹配内容 " + toDisplayPath(projectRoot.relativize(normalized));
            }
            String replaced = original.replace(oldContent, StrUtil.nullToEmpty(newContent));
            Files.writeString(normalized, replaced, StandardCharsets.UTF_8);
            return "文件修改成功：" + toDisplayPath(projectRoot.relativize(normalized));
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件修改失败");
        }
    }
}
