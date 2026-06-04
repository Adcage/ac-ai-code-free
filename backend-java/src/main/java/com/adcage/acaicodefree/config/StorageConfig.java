package com.adcage.acaicodefree.config;

import com.adcage.acaicodefree.config.properties.StorageProperties;
import jakarta.annotation.Resource;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 存储配置类。
 * 本地存储模式下配置静态资源映射。
 *
 * @author adcage
 */
@Configuration
@ConditionalOnProperty(prefix = "storage", name = "type", havingValue = "local")
@EnableConfigurationProperties(StorageProperties.class)
public class StorageConfig implements WebMvcConfigurer {

    @Resource
    private StorageProperties storageProperties;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        String localPath = storageProperties.getLocal().getPath();
        // 确保路径以 / 结尾
        if (!localPath.endsWith("/") && !localPath.endsWith("\\")) {
            localPath = localPath + "/";
        }
        // 将 file: 协议的路径映射到 /storage/**
        registry.addResourceHandler("/storage/**")
                .addResourceLocations("file:" + localPath);
    }
}
