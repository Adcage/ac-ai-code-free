package com.adcage.acaicodefree.config;

import com.adcage.acaicodefree.config.properties.WorkspaceProperties;
import com.adcage.acaicodefree.constant.AppConstant;
import jakarta.annotation.Resource;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.nio.file.Path;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Resource
    private WorkspaceProperties workspaceProperties;

    private static String toResourceLocation(String rawPath) {
        String normalized = Path.of(rawPath).toAbsolutePath().normalize().toString().replace("\\", "/");
        if (!normalized.endsWith("/")) {
            normalized += "/";
        }
        return "file:///" + normalized;
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/static/**")
                .addResourceLocations(
                        toResourceLocation(workspaceProperties.getAgentWorkspaceDir()),
                        toResourceLocation(AppConstant.CODE_OUTPUT_ROOT_DIR),
                        toResourceLocation(AppConstant.CODE_DEPLOY_ROOT_DIR)
                )
                .setCachePeriod(0);
    }
}
