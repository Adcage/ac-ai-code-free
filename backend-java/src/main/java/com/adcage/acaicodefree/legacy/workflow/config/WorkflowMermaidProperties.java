package com.adcage.acaicodefree.legacy.workflow.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "workflow.mermaid")
public class WorkflowMermaidProperties {

    private String command = "mmdc";

    private String tempDir = System.getProperty("java.io.tmpdir");
}
