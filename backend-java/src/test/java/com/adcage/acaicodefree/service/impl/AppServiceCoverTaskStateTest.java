package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.vo.app.AppVO;
import com.adcage.acaicodefree.service.ScreenshotService;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Map;

import static org.mockito.ArgumentMatchers.any;

class AppServiceCoverTaskStateTest {

    @Test
    void coverTask_shouldRetryAndBecomeSuccess() throws Exception {
        AppServiceImpl appService = Mockito.spy(new AppServiceImpl());
        ScreenshotService screenshotService = Mockito.mock(ScreenshotService.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setMaxRetries(2);
        screenshotProperties.setRetryDelayMillis(0L);

        ReflectionTestUtils.setField(appService, "screenshotService", screenshotService);
        ReflectionTestUtils.setField(appService, "screenshotProperties", screenshotProperties);
        ReflectionTestUtils.setField(appService, "serverPort", "8700");
        ReflectionTestUtils.setField(appService, "contextPath", "/api");
        Mockito.doReturn(true).when(appService).updateById(any(App.class));
        Mockito.when(screenshotService.generateAndUploadCover(Mockito.eq(1L), Mockito.anyString()))
                .thenThrow(new RuntimeException("first fail"))
                .thenReturn("https://cdn.example.com/cover.jpg");

        ReflectionTestUtils.invokeMethod(appService, "triggerCoverGenerationAsync", 1L, "abc123", null);
        waitForFinalState(appService, 1L);

        App app = new App();
        app.setId(1L);
        AppVO appVO = appService.getAppVO(app);
        Assertions.assertEquals("SUCCESS", appVO.getCoverTaskStatus());
        Assertions.assertEquals(2, appVO.getCoverRetryCount());
        Assertions.assertTrue(appVO.getCoverErrorMessage() == null || appVO.getCoverErrorMessage().isBlank());
    }

    @Test
    void coverTask_shouldRemainFailedAfterMaxRetries() throws Exception {
        AppServiceImpl appService = Mockito.spy(new AppServiceImpl());
        ScreenshotService screenshotService = Mockito.mock(ScreenshotService.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setMaxRetries(2);
        screenshotProperties.setRetryDelayMillis(0L);

        ReflectionTestUtils.setField(appService, "screenshotService", screenshotService);
        ReflectionTestUtils.setField(appService, "screenshotProperties", screenshotProperties);
        ReflectionTestUtils.setField(appService, "serverPort", "8700");
        ReflectionTestUtils.setField(appService, "contextPath", "/api");
        Mockito.when(screenshotService.generateAndUploadCover(Mockito.eq(2L), Mockito.anyString()))
                .thenThrow(new RuntimeException("always fail"));

        ReflectionTestUtils.invokeMethod(appService, "triggerCoverGenerationAsync", 2L, "def456", null);
        waitForFinalState(appService, 2L);

        Map<Long, Map<String, Object>> stateMap = (Map<Long, Map<String, Object>>) ReflectionTestUtils.getField(appService, "coverTaskStateMap");
        Assertions.assertNotNull(stateMap);
        Map<String, Object> state = stateMap.get(2L);
        Assertions.assertNotNull(state);
        Assertions.assertEquals("FAILED", state.get("status"));
        Assertions.assertEquals(2, state.get("retryCount"));
        Assertions.assertTrue(String.valueOf(state.get("errorMessage")).contains("always fail"));
    }

    @Test
    void coverTask_shouldSkipWhenCoverAlreadyExists() {
        AppServiceImpl appService = Mockito.spy(new AppServiceImpl());
        ScreenshotService screenshotService = Mockito.mock(ScreenshotService.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setMaxRetries(2);
        screenshotProperties.setRetryDelayMillis(0L);

        ReflectionTestUtils.setField(appService, "screenshotService", screenshotService);
        ReflectionTestUtils.setField(appService, "screenshotProperties", screenshotProperties);
        ReflectionTestUtils.setField(appService, "serverPort", "8700");
        ReflectionTestUtils.setField(appService, "contextPath", "/api");

        ReflectionTestUtils.invokeMethod(appService,
                "triggerCoverGenerationAsync",
                3L,
                "ghi789",
                "https://cdn.example.com/manual-cover.jpg");

        Map<Long, Map<String, Object>> stateMap = (Map<Long, Map<String, Object>>) ReflectionTestUtils.getField(appService, "coverTaskStateMap");
        Assertions.assertNotNull(stateMap);
        Map<String, Object> state = stateMap.get(3L);
        Assertions.assertNotNull(state);
        Assertions.assertEquals("SKIPPED", state.get("status"));
        Assertions.assertEquals(0, state.get("retryCount"));
        Assertions.assertEquals("", state.get("errorMessage"));
        Mockito.verifyNoInteractions(screenshotService);
    }

    private void waitForFinalState(AppServiceImpl appService, Long appId) throws Exception {
        for (int i = 0; i < 50; i++) {
            Map<Long, Map<String, Object>> stateMap = (Map<Long, Map<String, Object>>) ReflectionTestUtils.getField(appService, "coverTaskStateMap");
            if (stateMap != null && stateMap.get(appId) != null) {
                Object status = stateMap.get(appId).get("status");
                if ("SUCCESS".equals(status) || "FAILED".equals(status)) {
                    return;
                }
            }
            Thread.sleep(20L);
        }
        throw new AssertionError("等待封面任务状态超时");
    }
}
