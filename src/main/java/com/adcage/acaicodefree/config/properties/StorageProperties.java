package com.adcage.acaicodefree.config.properties;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 存储配置属性。
 * 支持 COS 和本地存储两种模式的配置。
 *
 * @author adcage
 */
@Data
@Component
@ConfigurationProperties(prefix = "storage")
public class StorageProperties {

    /**
     * 存储类型：cos 或 local，默认 local
     */
    private String type = "local";

    /**
     * 本地存储配置
     */
    private LocalConfig local = new LocalConfig();

    /**
     * 本地存储配置
     */
    @Data
    public static class LocalConfig {
        /**
         * 本地存储根目录，默认 ./storage
         */
        private String path = "./storage";

        /**
         * 访问 URL 前缀，默认 http://localhost:8700/api/storage
         */
        private String urlPrefix = "http://localhost:8700/api/storage";
    }
}
