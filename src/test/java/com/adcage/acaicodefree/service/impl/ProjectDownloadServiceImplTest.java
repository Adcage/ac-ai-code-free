package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.io.FileUtil;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletResponse;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

class ProjectDownloadServiceImplTest {

    private final ProjectDownloadServiceImpl projectDownloadService = new ProjectDownloadServiceImpl();

    @Test
    void writeProjectZipToResponse_shouldFilterExcludedFiles() throws IOException {
        File projectDir = FileUtil.createTempFile("project-download-test-", "", true);
        FileUtil.del(projectDir);
        FileUtil.mkdir(projectDir);
        FileUtil.writeString("console.log('ok')", Path.of(projectDir.getAbsolutePath(), "src", "main.js").toFile(), StandardCharsets.UTF_8);
        FileUtil.writeString("SECRET=1", Path.of(projectDir.getAbsolutePath(), ".env").toFile(), StandardCharsets.UTF_8);
        FileUtil.writeString("should skip", Path.of(projectDir.getAbsolutePath(), "dist", "index.html").toFile(), StandardCharsets.UTF_8);
        FileUtil.writeString("module", Path.of(projectDir.getAbsolutePath(), "node_modules", "x.js").toFile(), StandardCharsets.UTF_8);

        MockHttpServletResponse response = new MockHttpServletResponse();
        projectDownloadService.writeProjectZipToResponse(projectDir.toPath(), "app-test.zip", response);

        Assertions.assertEquals("application/zip", response.getContentType());
        String disposition = response.getHeader("Content-Disposition");
        Assertions.assertNotNull(disposition);
        Assertions.assertTrue(disposition.contains("app-test.zip"));
        byte[] zipBytes = response.getContentAsByteArray();
        Assertions.assertTrue(zipBytes.length > 0);
        Set<String> entryNames = unzipEntryNames(zipBytes);
        Assertions.assertTrue(entryNames.stream().anyMatch(name -> name.endsWith("src/main.js")));
        Assertions.assertFalse(entryNames.stream().anyMatch(name -> name.contains(".env")));
        Assertions.assertFalse(entryNames.stream().anyMatch(name -> name.contains("node_modules")));
        Assertions.assertFalse(entryNames.stream().anyMatch(name -> name.contains("dist/")));
        FileUtil.del(projectDir);
    }

    private Set<String> unzipEntryNames(byte[] zipBytes) throws IOException {
        Set<String> names = new HashSet<>();
        try (ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(zipBytes))) {
            ZipEntry entry;
            while ((entry = zipInputStream.getNextEntry()) != null) {
                names.add(entry.getName());
            }
        }
        return names;
    }
}
