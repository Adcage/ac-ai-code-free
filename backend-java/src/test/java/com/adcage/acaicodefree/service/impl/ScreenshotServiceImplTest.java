package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.io.FileUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.mapper.AppMapper;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.storage.FileStorageStrategy;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;

class ScreenshotServiceImplTest {

    // ========== generateAndUploadCover 测试 ==========

    @Test
    void generateAndUploadCover_shouldUploadAndCleanupTempFile() {
        FileStorageStrategy fileStorageStrategy = Mockito.mock(FileStorageStrategy.class);
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
        ReflectionTestUtils.setField(screenshotService, "fileStorageStrategy", fileStorageStrategy);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", screenshotProperties);
        Mockito.when(fileStorageStrategy.uploadFile(Mockito.anyString(), Mockito.eq(tempFile)))
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

    // ========== triggerCoverGenerationIfNeeded 测试 ==========

    @Test
    void coverTask_shouldRetryAndBecomeSuccess() throws Exception {
        ScreenshotServiceImpl screenshotService = Mockito.spy(new ScreenshotServiceImpl());
        AppMapper appMapper = Mockito.mock(AppMapper.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setMaxRetries(2);
        screenshotProperties.setRetryDelayMillis(0L);

        ReflectionTestUtils.setField(screenshotService, "appMapper", appMapper);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", screenshotProperties);
        ReflectionTestUtils.setField(screenshotService, "serverPort", "8700");
        ReflectionTestUtils.setField(screenshotService, "contextPath", "/api");

        App app = new App();
        app.setId(1L);
        app.setDeployKey("abc123");
        Mockito.when(appMapper.selectOneById(1L)).thenReturn(app);
        Mockito.when(appMapper.update(any(App.class))).thenReturn(1);

        // mock generateAndUploadCover: first fail, then success
        Mockito.doThrow(new RuntimeException("first fail"))
                .doReturn("https://cdn.example.com/cover.jpg")
                .when(screenshotService).generateAndUploadCover(Mockito.eq(1L), Mockito.anyString());

        screenshotService.triggerCoverGenerationIfNeeded(1L, 100L);
        waitForFinalState(screenshotService, 1L);

        Map<String, Object> state = screenshotService.getCoverTaskState(1L);
        Assertions.assertNotNull(state);
        Assertions.assertEquals("SUCCESS", state.get("status"));
        Assertions.assertEquals(2, state.get("retryCount"));
    }

    @Test
    void coverTask_shouldRemainFailedAfterMaxRetries() throws Exception {
        ScreenshotServiceImpl screenshotService = Mockito.spy(new ScreenshotServiceImpl());
        AppMapper appMapper = Mockito.mock(AppMapper.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setMaxRetries(2);
        screenshotProperties.setRetryDelayMillis(0L);

        ReflectionTestUtils.setField(screenshotService, "appMapper", appMapper);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", screenshotProperties);
        ReflectionTestUtils.setField(screenshotService, "serverPort", "8700");
        ReflectionTestUtils.setField(screenshotService, "contextPath", "/api");

        App app = new App();
        app.setId(2L);
        app.setDeployKey("def456");
        Mockito.when(appMapper.selectOneById(2L)).thenReturn(app);

        Mockito.doThrow(new RuntimeException("always fail"))
                .when(screenshotService).generateAndUploadCover(Mockito.eq(2L), Mockito.anyString());

        screenshotService.triggerCoverGenerationIfNeeded(2L, 200L);
        waitForFinalState(screenshotService, 2L);

        Map<String, Object> state = screenshotService.getCoverTaskState(2L);
        Assertions.assertNotNull(state);
        Assertions.assertEquals("FAILED", state.get("status"));
        Assertions.assertEquals(2, state.get("retryCount"));
    }

    @Test
    void coverTask_shouldSkipWhenSameAgentRunAlreadyRunning() {
        ScreenshotServiceImpl screenshotService = new ScreenshotServiceImpl();
        AppMapper appMapper = Mockito.mock(AppMapper.class);

        ReflectionTestUtils.setField(screenshotService, "appMapper", appMapper);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", new ScreenshotProperties());

        // 模拟已有 RUNNING 状态（同一 agentRunId）
        Map<Long, Map<String, Object>> stateMap =
                (Map<Long, Map<String, Object>>) ReflectionTestUtils.getField(screenshotService, "coverTaskStateMap");
        Map<String, Object> runningState = new java.util.HashMap<>();
        runningState.put("status", "RUNNING");
        runningState.put("agentRunId", 100L);
        runningState.put("retryCount", 1);
        stateMap.put(3L, runningState);

        // 同一 agentRunId 再次触发 → 应跳过
        screenshotService.triggerCoverGenerationIfNeeded(3L, 100L);

        // 不应调用 appMapper.selectOneById
        Mockito.verifyNoInteractions(appMapper);
    }

    @Test
    void coverTask_shouldAllowDifferentAgentRun() {
        ScreenshotServiceImpl screenshotService = Mockito.spy(new ScreenshotServiceImpl());
        AppMapper appMapper = Mockito.mock(AppMapper.class);

        ReflectionTestUtils.setField(screenshotService, "appMapper", appMapper);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", new ScreenshotProperties());
        ReflectionTestUtils.setField(screenshotService, "serverPort", "8700");
        ReflectionTestUtils.setField(screenshotService, "contextPath", "/api");

        // 模拟已有 SUCCESS 状态（旧 agentRunId）
        Map<Long, Map<String, Object>> stateMap =
                (Map<Long, Map<String, Object>>) ReflectionTestUtils.getField(screenshotService, "coverTaskStateMap");
        Map<String, Object> successState = new java.util.HashMap<>();
        successState.put("status", "SUCCESS");
        successState.put("agentRunId", 100L);
        successState.put("retryCount", 1);
        stateMap.put(4L, successState);

        App app = new App();
        app.setId(4L);
        app.setDeployKey("new456");
        Mockito.when(appMapper.selectOneById(4L)).thenReturn(app);

        // 不同 agentRunId → 应允许重新截图
        screenshotService.triggerCoverGenerationIfNeeded(4L, 200L);

        // 应调用 appMapper.selectOneById（说明进入了截图逻辑）
        Mockito.verify(appMapper).selectOneById(4L);
    }

    @Test
    void coverTask_shouldSkipWhenNoPreviewUrl() {
        ScreenshotServiceImpl screenshotService = Mockito.spy(new ScreenshotServiceImpl());
        AppMapper appMapper = Mockito.mock(AppMapper.class);

        ReflectionTestUtils.setField(screenshotService, "appMapper", appMapper);
        ReflectionTestUtils.setField(screenshotService, "screenshotProperties", new ScreenshotProperties());
        ReflectionTestUtils.setField(screenshotService, "serverPort", "8700");
        ReflectionTestUtils.setField(screenshotService, "contextPath", "/api");

        // 没有 deployKey 且 codeGenType 为 null → 无预览 URL
        App app = new App();
        app.setId(5L);
        Mockito.when(appMapper.selectOneById(5L)).thenReturn(app);

        screenshotService.triggerCoverGenerationIfNeeded(5L, 300L);

        // 不应调用 generateAndUploadCover
        Mockito.verify(screenshotService, Mockito.never()).generateAndUploadCover(Mockito.anyLong(), Mockito.anyString());
    }

    private void waitForFinalState(ScreenshotServiceImpl screenshotService, Long appId) throws Exception {
        for (int i = 0; i < 50; i++) {
            Map<String, Object> state = screenshotService.getCoverTaskState(appId);
            if (state != null) {
                Object status = state.get("status");
                if ("SUCCESS".equals(status) || "FAILED".equals(status)) {
                    return;
                }
            }
            Thread.sleep(20L);
        }
        throw new AssertionError("等待封面任务状态超时");
    }
}
