package com.adcage.acaicodefree.ai.tools;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

class FileModifyToolTest {

    @TempDir
    Path tempDir;

    @Test
    void modifyFileShouldReplaceMatchedContent() throws Exception {
        FileModifyTool fileModifyTool = createTool();
        Path targetFile = tempDir.resolve("vue_project_1").resolve("src/App.vue");
        Files.createDirectories(targetFile.getParent());
        Files.writeString(targetFile, "<h1>旧标题</h1>", StandardCharsets.UTF_8);

        String result = fileModifyTool.modifyFile("src/App.vue", "旧标题", "新标题", 1L);

        Assertions.assertEquals("文件修改成功：src/App.vue", result);
        Assertions.assertEquals("<h1>新标题</h1>", Files.readString(targetFile, StandardCharsets.UTF_8));
    }

    @Test
    void modifyFileShouldReturnFailureMessageWhenOldContentMissing() throws Exception {
        FileModifyTool fileModifyTool = createTool();
        Path targetFile = tempDir.resolve("vue_project_1").resolve("src/App.vue");
        Files.createDirectories(targetFile.getParent());
        Files.writeString(targetFile, "<h1>不匹配内容</h1>", StandardCharsets.UTF_8);

        String result = fileModifyTool.modifyFile("src/App.vue", "旧标题", "新标题", 1L);

        Assertions.assertTrue(result.startsWith("文件修改失败：未找到匹配内容"));
        Assertions.assertEquals("<h1>不匹配内容</h1>", Files.readString(targetFile, StandardCharsets.UTF_8));
    }

    private FileModifyTool createTool() {
        FileModifyTool fileModifyTool = new FileModifyTool();
        ReflectionTestUtils.setField(fileModifyTool, "codeOutputRootPath", tempDir);
        return fileModifyTool;
    }
}
