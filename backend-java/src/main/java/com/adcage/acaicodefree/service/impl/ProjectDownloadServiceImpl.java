package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.io.IoUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.core.util.ZipUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.service.ProjectDownloadService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Set;

@Service
public class ProjectDownloadServiceImpl implements ProjectDownloadService {

    private static final Set<String> EXCLUDED_DIRS = Set.of(
            "node_modules", ".git", "dist", "build", "target", ".mvn", ".idea", ".vscode", ".cache");

    private static final Set<String> EXCLUDED_FILE_NAMES = Set.of(".ds_store", ".env");

    private static final Set<String> EXCLUDED_FILE_EXTENSIONS = Set.of(".log", ".tmp", ".cache");

    @Override
    public void writeProjectZipToResponse(Path sourceDir, String fileName, HttpServletResponse response) {
        File sourceFile = sourceDir == null ? null : sourceDir.toFile();
        if (sourceFile == null || !sourceFile.exists() || !sourceFile.isDirectory()) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "源码目录不存在");
        }
        String safeFileName = StrUtil.blankToDefault(fileName, "app.zip");
        File tempZipFile = null;
        try {
            tempZipFile = FileUtil.createTempFile("app-download-", ".zip", true);
            ZipUtil.zip(tempZipFile, StandardCharsets.UTF_8, true, this::shouldInclude, sourceFile);
            response.setContentType("application/zip");
            response.setHeader("Content-Disposition", buildContentDisposition(safeFileName));
            response.setContentLengthLong(tempZipFile.length());
            try (InputStream inputStream = FileUtil.getInputStream(tempZipFile)) {
                IoUtil.copy(inputStream, response.getOutputStream());
                response.flushBuffer();
            }
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "下载源码失败: " + e.getMessage());
        } finally {
            if (tempZipFile != null && tempZipFile.exists()) {
                FileUtil.del(tempZipFile);
            }
        }
    }

    private boolean shouldInclude(File file) {
        if (file == null) {
            return false;
        }
        String lowerName = file.getName().toLowerCase(Locale.ROOT);
        if (file.isDirectory()) {
            return !EXCLUDED_DIRS.contains(lowerName);
        }
        if (EXCLUDED_FILE_NAMES.contains(lowerName)) {
            return false;
        }
        for (String extension : EXCLUDED_FILE_EXTENSIONS) {
            if (lowerName.endsWith(extension)) {
                return false;
            }
        }
        return true;
    }

    private String buildContentDisposition(String fileName) {
        String encodedName = URLEncoder.encode(fileName, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        return "attachment; filename*=UTF-8''" + encodedName;
    }
}
