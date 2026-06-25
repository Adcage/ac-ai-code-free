package com.adcage.acaicodefree.scheduler;

import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import com.adcage.acaicodefree.mapper.AgentRunMapper;
import com.adcage.acaicodefree.service.ScreenshotService;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.never;

class CoverGenerationSchedulerTest {

    @Test
    void scan_shouldTriggerForActiveAppsWithoutCover() {
        CoverGenerationScheduler scheduler = new CoverGenerationScheduler();
        AgentRunMapper agentRunMapper = Mockito.mock(AgentRunMapper.class);
        ScreenshotService screenshotService = Mockito.mock(ScreenshotService.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();
        screenshotProperties.setCoverScanLookbackHours(24);

        Mockito.when(agentRunMapper.selectRecentActiveAppIds(24))
                .thenReturn(List.of(1L, 2L, 3L));

        injectFields(scheduler, agentRunMapper, screenshotService, screenshotProperties);

        scheduler.scanAndTriggerCoverGeneration();

        Mockito.verify(screenshotService, Mockito.times(3)).triggerCoverGenerationIfNeeded(anyLong(), Mockito.isNull());
    }

    @Test
    void scan_shouldHandleEmptyResult() {
        CoverGenerationScheduler scheduler = new CoverGenerationScheduler();
        AgentRunMapper agentRunMapper = Mockito.mock(AgentRunMapper.class);
        ScreenshotService screenshotService = Mockito.mock(ScreenshotService.class);
        ScreenshotProperties screenshotProperties = new ScreenshotProperties();

        Mockito.when(agentRunMapper.selectRecentActiveAppIds(24))
                .thenReturn(List.of());

        injectFields(scheduler, agentRunMapper, screenshotService, screenshotProperties);

        scheduler.scanAndTriggerCoverGeneration();

        Mockito.verify(screenshotService, never()).triggerCoverGenerationIfNeeded(anyLong(), any());
    }

    private void injectFields(CoverGenerationScheduler scheduler,
                              AgentRunMapper agentRunMapper,
                              ScreenshotService screenshotService,
                              ScreenshotProperties screenshotProperties) {
        try {
            java.lang.reflect.Field mapperField = CoverGenerationScheduler.class.getDeclaredField("agentRunMapper");
            mapperField.setAccessible(true);
            mapperField.set(scheduler, agentRunMapper);

            java.lang.reflect.Field serviceField = CoverGenerationScheduler.class.getDeclaredField("screenshotService");
            serviceField.setAccessible(true);
            serviceField.set(scheduler, screenshotService);

            java.lang.reflect.Field propsField = CoverGenerationScheduler.class.getDeclaredField("screenshotProperties");
            propsField.setAccessible(true);
            propsField.set(scheduler, screenshotProperties);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
