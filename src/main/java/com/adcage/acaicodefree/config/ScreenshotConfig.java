package com.adcage.acaicodefree.config;

import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(ScreenshotProperties.class)
public class ScreenshotConfig {
}
