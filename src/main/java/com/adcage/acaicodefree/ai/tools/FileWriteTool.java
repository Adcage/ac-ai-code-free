package com.adcage.acaicodefree.ai.tools;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.exception.BusinessException;
import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.ToolMemoryId;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

@Component
public class FileWriteTool {

    private Path codeOutputRootPath = AppConstant.getCodeOutputRootPath();

    @Tool("写入文件到指定路径")
    public String writeFile(String relativeFilePath, String content, @ToolMemoryId Long appId) {
        if (appId == null || appId <= 0) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用 ID 非法");
        }
        if (relativeFilePath == null || relativeFilePath.isBlank()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "文件路径不能为空");
        }
        Path relativePath = Path.of(relativeFilePath);
        if (relativePath.isAbsolute()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "非法文件路径");
        }
        Path projectRoot = codeOutputRootPath.resolve(AppConstant.VUE_PROJECT_OUTPUT_PREFIX + appId).normalize();
        Path normalized = projectRoot.resolve(relativePath).normalize();
        if (!normalized.startsWith(projectRoot)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "非法文件路径");
        }
        try {
            Path parent = normalized.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(normalized, content == null ? "" : content, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件写入失败");
        }
        return "文件写入成功：" + relativePath.toString().replace('\\', '/');
    }
}
