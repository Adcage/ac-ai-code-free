package com.adcage.acaicodefree.legacy.workflow.tool;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.legacy.workflow.model.ImageCategoryEnum;
import com.adcage.acaicodefree.legacy.workflow.model.ImageResource;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

@Slf4j
public class MermaidDiagramTool {

    @FunctionalInterface
    public interface MermaidCommandExecutor {
        int execute(List<String> command, Path outputFile) throws Exception;
    }

    private final ObjectStorageManager objectStorageManager;

    private final String command;

    private final String tempDir;

    private final MermaidCommandExecutor commandExecutor;

    public MermaidDiagramTool(ObjectStorageManager objectStorageManager,
                              String command,
                              String tempDir,
                              MermaidCommandExecutor commandExecutor) {
        this.objectStorageManager = objectStorageManager;
        this.command = command;
        this.tempDir = tempDir;
        this.commandExecutor = commandExecutor;
    }

    public List<ImageResource> renderArchitectureDiagram(String mermaidContent, String description) {
        if (StrUtil.isBlank(mermaidContent)) {
            return Collections.emptyList();
        }
        Path inputFile = null;
        Path outputFile = null;
        try {
            Files.createDirectories(Path.of(tempDir));
            String fileId = UUID.randomUUID().toString();
            inputFile = Path.of(tempDir, fileId + ".mmd");
            outputFile = Path.of(tempDir, fileId + ".png");
            Files.writeString(inputFile, mermaidContent, StandardCharsets.UTF_8);
            int exitCode = commandExecutor.execute(buildCommand(inputFile, outputFile), outputFile);
            if (exitCode != 0 || !Files.exists(outputFile)) {
                log.warn("[MermaidDiagramTool] render failed, command={}, exitCode={}", command, exitCode);
                return Collections.emptyList();
            }
            String objectKey = "/workflow/mermaid/" + outputFile.getFileName();
            String url = objectStorageManager.uploadFile(objectKey, outputFile.toFile());
            return List.of(ImageResource.builder()
                    .category(ImageCategoryEnum.ARCHITECTURE)
                    .description(StrUtil.blankToDefault(description, "Mermaid architecture diagram"))
                    .url(url)
                    .build());
        } catch (Exception e) {
            log.warn("[MermaidDiagramTool] render failed, command={}", command, e);
            return Collections.emptyList();
        } finally {
            deleteIfExists(inputFile);
            deleteIfExists(outputFile);
        }
    }

    private List<String> buildCommand(Path inputFile, Path outputFile) {
        return List.of(command, "-i", inputFile.toString(), "-o", outputFile.toString());
    }

    private void deleteIfExists(Path file) {
        if (file == null) {
            return;
        }
        try {
            Files.deleteIfExists(file);
        } catch (IOException e) {
            log.debug("[MermaidDiagramTool] failed to delete temp file: {}", file, e);
        }
    }
}
