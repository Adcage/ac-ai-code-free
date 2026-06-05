package com.adcage.acaicodefree.service;

import java.nio.file.Path;

public interface AgentWorkspaceService {

    Path initWorkspace(Long agentRunId, Long appId);

    Path getWorkspaceSourceDir(Long agentRunId);

    void cleanupWorkspace(Long agentRunId);
}
