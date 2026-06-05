package com.adcage.acaicodefree.config.properties;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "app.workspace")
public class WorkspaceProperties {

    private String codeOutputDir = "../temp/code_output";

    private String codeDeployDir = "../temp/code_deploy";

    private String agentWorkspaceDir = "../storage/agent-workspaces";
}
