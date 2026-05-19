package com.adcage.acaicodefree.workflow.tool;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.workflow.model.ImageCategoryEnum;
import com.adcage.acaicodefree.workflow.model.ImageResource;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

@Slf4j
public class LogoGeneratorTool {

    @FunctionalInterface
    public interface LogoClient {
        String generateImageUrl(String prompt) throws Exception;
    }

    @FunctionalInterface
    public interface FileDownloader {
        void download(String url, Path targetFile) throws Exception;
    }

    private final String apiKey;

    private final String tempDir;

    private final ObjectStorageManager objectStorageManager;

    private final LogoClient logoClient;

    private final FileDownloader fileDownloader;

    public LogoGeneratorTool(String apiKey,
                             String tempDir,
                             ObjectStorageManager objectStorageManager,
                             LogoClient logoClient,
                             FileDownloader fileDownloader) {
        this.apiKey = apiKey;
        this.tempDir = tempDir;
        this.objectStorageManager = objectStorageManager;
        this.logoClient = logoClient;
        this.fileDownloader = fileDownloader;
    }

    public List<ImageResource> generateLogo(String prompt) {
        if (StrUtil.isBlank(prompt) || StrUtil.isBlank(apiKey)) {
            return Collections.emptyList();
        }
        Path tempFile = null;
        try {
            String imageUrl = logoClient.generateImageUrl(prompt);
            if (StrUtil.isBlank(imageUrl)) {
                return Collections.emptyList();
            }
            Files.createDirectories(Path.of(tempDir));
            tempFile = Path.of(tempDir, UUID.randomUUID() + ".png");
            fileDownloader.download(imageUrl, tempFile);
            String objectKey = "/workflow/logo/" + tempFile.getFileName();
            String uploadedUrl = objectStorageManager.uploadFile(objectKey, tempFile.toFile());
            return List.of(ImageResource.builder()
                    .category(ImageCategoryEnum.LOGO)
                    .description("Logo for " + prompt)
                    .url(uploadedUrl)
                    .build());
        } catch (Exception e) {
            log.warn("[LogoGeneratorTool] generate logo failed, prompt={}", prompt, e);
            return Collections.emptyList();
        } finally {
            deleteIfExists(tempFile);
        }
    }

    private void deleteIfExists(Path file) {
        if (file == null) {
            return;
        }
        try {
            Files.deleteIfExists(file);
        } catch (IOException e) {
            log.debug("[LogoGeneratorTool] failed to delete temp file: {}", file, e);
        }
    }
}
