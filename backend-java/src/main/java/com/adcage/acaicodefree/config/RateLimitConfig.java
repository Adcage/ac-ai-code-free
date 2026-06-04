package com.adcage.acaicodefree.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "app.rate-limit")
public class RateLimitConfig {

    private AiChat aiChat = new AiChat();

    @Data
    public static class AiChat {
        private int userRate = 5;
        private int userIntervalSeconds = 60;
        private int ipRate = 3;
        private int ipIntervalSeconds = 60;
    }
}
