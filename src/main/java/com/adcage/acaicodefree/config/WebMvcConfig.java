package com.adcage.acaicodefree.config;

import com.adcage.acaicodefree.constant.AppConstant;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.io.File;

/**
 * 静态资源映射配置
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 1. 映射生成目录 (CODE_OUTPUT_ROOT_DIR)
        String outputPath = AppConstant.CODE_OUTPUT_ROOT_DIR.replace("\\", "/");
        if (!outputPath.endsWith("/")) {
            outputPath += "/";
        }
        String outputLocation = "file:///" + outputPath;

        // 2. 映射部署目录 (CODE_DEPLOY_ROOT_DIR)
        String deployPath = AppConstant.CODE_DEPLOY_ROOT_DIR.replace("\\", "/");
        if (!deployPath.endsWith("/")) {
            deployPath += "/";
        }
        String deployLocation = "file:///" + deployPath;

        // 将 /static/** 映射到本地目录（支持从两个目录中查找）
        registry.addResourceHandler("/static/**")
                .addResourceLocations(outputLocation, deployLocation)
                .setCachePeriod(0);
    }
}
