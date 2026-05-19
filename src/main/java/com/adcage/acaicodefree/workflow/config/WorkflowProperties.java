package com.adcage.acaicodefree.workflow.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "app.codegen.workflow")
public class WorkflowProperties {

    private boolean enabled = false;

    private String mode = "legacy";

    private int maxImageCount = 24;

    private int imageSummaryLimit = 12;

    private boolean enableParallelImageCollect = false;

    public boolean useWorkflow() {
        return enabled && "workflow".equalsIgnoreCase(mode);
    }
}
