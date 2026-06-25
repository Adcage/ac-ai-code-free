package com.adcage.acaicodefree.scheduler;

import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import com.adcage.acaicodefree.mapper.AgentRunMapper;
import com.adcage.acaicodefree.service.ScreenshotService;
import jakarta.annotation.Resource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class CoverGenerationScheduler {

    private static final Logger log = LoggerFactory.getLogger(CoverGenerationScheduler.class);

    @Resource
    private AgentRunMapper agentRunMapper;

    @Resource
    private ScreenshotService screenshotService;

    @Resource
    private ScreenshotProperties screenshotProperties;

    /**
     * 定时扫描最近活跃但没有封面的应用，触发截图兜底。
     * 默认每 5 分钟执行一次。
     */
    @Scheduled(fixedDelayString = "${app.screenshot.cover-scan-interval-ms:300000}")
    public void scanAndTriggerCoverGeneration() {
        int lookbackHours = screenshotProperties.getCoverScanLookbackHours() != null
                ? screenshotProperties.getCoverScanLookbackHours() : 24;

        List<Long> activeAppIds;
        try {
            activeAppIds = agentRunMapper.selectRecentActiveAppIds(lookbackHours);
        } catch (Exception e) {
            log.error("封面兜底扫描查询失败", e);
            return;
        }

        if (activeAppIds == null || activeAppIds.isEmpty()) {
            return;
        }

        int triggered = 0;
        for (Long appId : activeAppIds) {
            try {
                // triggerCoverGenerationIfNeeded 内部会检查是否需要截图
                screenshotService.triggerCoverGenerationIfNeeded(appId, null);
                triggered++;
            } catch (Exception e) {
                log.warn("封面兜底扫描触发失败, appId={}", appId, e);
            }
        }

        if (triggered > 0) {
            log.info("封面兜底扫描完成, 扫描应用数={}, 触发截图数={}", activeAppIds.size(), triggered);
        }
    }
}
