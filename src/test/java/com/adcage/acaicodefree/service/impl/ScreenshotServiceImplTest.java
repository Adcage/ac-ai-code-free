package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.io.FileUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.manager.CosManager;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.File;
import java.nio.charset.StandardCharsets;

class ScreenshotServiceImplTest {

    @Test
    void generateAndUploadCover_shouldUploadAndCleanupTempFile() {
        CosManager cosManager = Mockito.mock(CosManager.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setUploadPrefix("/screenshots");

        File tempFile = FileUtil.createTempFile("screenshot-test-", "_compressed.jpg", true);
        FileUtil.writeString("test", tempFile, StandardCharsets.UTF_8);

        ScreenshotServiceImpl screenshotService = new ScreenshotServiceImpl() {
            @Override
            File captureCompressedFile(String appUrl) {
                return tempFile;
            }
        };
        ReflectionTestUtils.setField(screenshotService, "cosManager", cosManager);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", screenshotProperties);
        Mockito.when(cosManager.uploadFile(Mockito.anyString(), Mockito.eq(tempFile)))
                .thenReturn("https://cdn.example.com/screenshots/test.jpg");

        String url = screenshotService.generateAndUploadCover(1L, "http://localhost/app");
        Assertions.assertEquals("https://cdn.example.com/screenshots/test.jpg", url);
        Assertions.assertFalse(tempFile.exists(), "上传完成后应删除临时文件");
    }

    @Test
    void generateAndUploadCover_shouldThrowWhenAppIdInvalid() {
        ScreenshotServiceImpl screenshotService = new ScreenshotServiceImpl();
        BusinessException exception = Assertions.assertThrows(BusinessException.class,
                () -> screenshotService.generateAndUploadCover(0L, "http://localhost/app"));
        Assertions.assertEquals(ErrorCode.PARAMS_ERROR.getCode(), exception.getCode());
    }
}
